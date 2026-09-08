#!/usr/bin/env python3
"""
item_dbc_tool.py
Safe helper for WoW 3.3.5a Item.dbc (WDBC).

Typical MorphSummon use:
    python3 item_dbc_tool.py Item.dbc \
        --ids 91001-91079 \
        --clone 22450 \
        --output Item_morphsummon.dbc

Or read UnlockItemID values directly from the MorphSummon catalog SQL:
    python3 item_dbc_tool.py Item.dbc \
        --catalog-sql mod_morphsummon_unlock_catalog_template_v3.sql \
        --clone 22450 \
        --output Item_morphsummon.dbc

The tool preserves the string block and all existing records. New records are
created by copying the full source record byte-for-byte and replacing only ID.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

HEADER_SIZE = 20
WDBC_MAGIC = b"WDBC"


@dataclass(frozen=True)
class DBCHeader:
    record_count: int
    field_count: int
    record_size: int
    string_block_size: int


class DBCError(RuntimeError):
    pass


def read_dbc(path: Path):
    data = path.read_bytes()

    if len(data) < HEADER_SIZE:
        raise DBCError(f"{path}: file is too small to be a DBC")

    if data[:4] != WDBC_MAGIC:
        raise DBCError(
            f"{path}: unsupported magic {data[:4]!r}; expected {WDBC_MAGIC!r}"
        )

    header = DBCHeader(*struct.unpack_from("<4I", data, 4))
    expected_size = (
        HEADER_SIZE
        + header.record_count * header.record_size
        + header.string_block_size
    )

    if len(data) != expected_size:
        raise DBCError(
            f"{path}: size mismatch: header expects {expected_size} bytes, "
            f"file has {len(data)} bytes"
        )

    # This tool is intentionally strict for the 3.3.5a Item.dbc layout.
    if header.field_count != 8 or header.record_size != 32:
        raise DBCError(
            "This does not look like a WoW 3.3.5a Item.dbc: "
            f"field_count={header.field_count}, record_size={header.record_size}. "
            "Expected 8 fields / 32 bytes."
        )

    records = []
    ids = set()

    pos = HEADER_SIZE
    for _ in range(header.record_count):
        raw = data[pos:pos + header.record_size]
        item_id = struct.unpack_from("<I", raw, 0)[0]

        if item_id in ids:
            raise DBCError(f"Duplicate Item.dbc ID detected: {item_id}")

        ids.add(item_id)
        records.append((item_id, raw))
        pos += header.record_size

    string_block = data[pos:pos + header.string_block_size]

    return header, records, string_block


def parse_id_spec(specs: Iterable[str]) -> set[int]:
    result: set[int] = set()

    for spec in specs:
        for token in spec.split(","):
            token = token.strip()
            if not token:
                continue

            if "-" in token:
                left, right = token.split("-", 1)
                start = int(left, 0)
                end = int(right, 0)
                if end < start:
                    raise ValueError(f"Invalid descending range: {token}")
                result.update(range(start, end + 1))
            else:
                result.add(int(token, 0))

    return result


def ids_from_catalog_sql(path: Path) -> set[int]:
    """
    Extract the 5th value (UnlockItemID) from catalog rows shaped like:
      (MorphType, MorphID, 'Category', 'AppearanceName',
       UnlockItemID, IsDefault, ...)

    This targets the MorphSummon catalog templates produced for this project.
    """
    text = path.read_text(encoding="utf-8")

    pattern = re.compile(
        r"""^\s*\(
            \s*\d+\s*,                    # MorphType
            \s*\d+\s*,                    # MorphID
            \s*'(?:''|[^'])*'\s*,         # Category
            \s*'(?:''|[^'])*'\s*,         # AppearanceName
            \s*(\d+)\s*,                  # UnlockItemID
            \s*[01]\s*,                   # IsDefault
        """,
        re.MULTILINE | re.VERBOSE,
    )

    ids = {int(m.group(1)) for m in pattern.finditer(text)}
    ids.discard(0)

    if not ids:
        raise DBCError(
            f"No UnlockItemID values were found in catalog SQL: {path}"
        )

    return ids


def mapping_from_csv(path: Path) -> dict[int, int]:
    """
    Optional advanced mode.

    CSV format:
        item_id,clone_id
        91001,22450
        91002,22450
        92000,6948
    """
    mapping: dict[int, int] = {}

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"item_id", "clone_id"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise DBCError(
                f"{path}: CSV needs columns: item_id,clone_id"
            )

        for row in reader:
            item_id = int(row["item_id"], 0)
            clone_id = int(row["clone_id"], 0)
            mapping[item_id] = clone_id

    return mapping


def describe_record(raw: bytes) -> tuple[int, ...]:
    # Item.dbc 3.3.5a = 8 signed/unsigned 32-bit values.
    # We display fields 4 etc. as signed because -1 is meaningful.
    return struct.unpack("<IiiiIiII", raw)


def write_dbc(
    source: Path,
    output: Path,
    ids_to_clone: dict[int, int],
    replace_existing: bool,
    dry_run: bool,
):
    header, record_list, string_block = read_dbc(source)
    records = {item_id: raw for item_id, raw in record_list}

    added = []
    replaced = []
    skipped = []

    missing_clone_ids = sorted(
        {clone_id for clone_id in ids_to_clone.values() if clone_id not in records}
    )
    if missing_clone_ids:
        raise DBCError(
            "Clone source ID(s) not present in Item.dbc: "
            + ", ".join(map(str, missing_clone_ids))
        )

    for item_id, clone_id in sorted(ids_to_clone.items()):
        if item_id <= 0 or item_id > 0xFFFFFFFF:
            raise DBCError(f"Invalid item ID: {item_id}")

        if item_id in records and not replace_existing:
            skipped.append(item_id)
            continue

        clone_raw = records[clone_id]
        new_raw = struct.pack("<I", item_id) + clone_raw[4:]

        if item_id in records:
            replaced.append(item_id)
        else:
            added.append(item_id)

        records[item_id] = new_raw

    sorted_records = sorted(records.items())

    if dry_run:
        return header, records, added, replaced, skipped

    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("wb") as f:
        f.write(WDBC_MAGIC)
        f.write(
            struct.pack(
                "<4I",
                len(sorted_records),
                header.field_count,
                header.record_size,
                len(string_block),
            )
        )
        for _, raw in sorted_records:
            f.write(raw)
        f.write(string_block)

    # Re-open and validate our own output.
    new_header, new_records, new_strings = read_dbc(output)

    if new_header.record_count != len(sorted_records):
        raise DBCError("Post-write validation failed: record count")
    if new_strings != string_block:
        raise DBCError("Post-write validation failed: string block changed")
    if [x[0] for x in new_records] != sorted(x[0] for x in new_records):
        raise DBCError("Post-write validation failed: records are not sorted")

    return new_header, dict(new_records), added, replaced, skipped


def build_parser():
    p = argparse.ArgumentParser(
        description="Safely add custom rows to a WoW 3.3.5a Item.dbc."
    )
    p.add_argument("dbc", type=Path, help="Source Item.dbc")
    p.add_argument(
        "--ids",
        action="append",
        default=[],
        metavar="SPEC",
        help="IDs/ranges, e.g. 91001-91079 or 91001,91005. Repeatable.",
    )
    p.add_argument(
        "--catalog-sql",
        type=Path,
        help="Extract UnlockItemID values from the MorphSummon catalog SQL.",
    )
    p.add_argument(
        "--clone",
        type=lambda x: int(x, 0),
        default=22450,
        help="Existing Item.dbc row to clone for --ids/--catalog-sql (default: 22450).",
    )
    p.add_argument(
        "--mapping-csv",
        type=Path,
        help="Advanced: CSV with item_id,clone_id columns.",
    )
    p.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output DBC. Default: <source>_patched.dbc",
    )
    p.add_argument(
        "--replace",
        action="store_true",
        help="Replace IDs that already exist. Default is to skip them.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report without writing anything.",
    )
    p.add_argument(
        "--info",
        action="store_true",
        help="Print source DBC information and exit if no add options are supplied.",
    )
    return p


def main() -> int:
    args = build_parser().parse_args()

    try:
        header, records_list, string_block = read_dbc(args.dbc)
        records = dict(records_list)

        if args.info:
            ids = [x[0] for x in records_list]
            print(f"File:              {args.dbc}")
            print(f"Magic:             WDBC")
            print(f"Records:           {header.record_count}")
            print(f"Fields:            {header.field_count}")
            print(f"Record size:       {header.record_size} bytes")
            print(f"String block:      {header.string_block_size} bytes")
            print(f"Min/Max Item ID:   {min(ids)} / {max(ids)}")
            print(f"IDs sorted:        {ids == sorted(ids)}")
            if args.clone in records:
                print(f"Clone {args.clone}:     {describe_record(records[args.clone])}")
            print()

        mapping: dict[int, int] = {}

        if args.ids:
            for item_id in parse_id_spec(args.ids):
                mapping[item_id] = args.clone

        if args.catalog_sql:
            for item_id in ids_from_catalog_sql(args.catalog_sql):
                mapping[item_id] = args.clone

        if args.mapping_csv:
            mapping.update(mapping_from_csv(args.mapping_csv))

        if not mapping:
            if args.info:
                return 0
            raise DBCError(
                "Nothing to add. Use --ids, --catalog-sql or --mapping-csv."
            )

        output = args.output
        if output is None:
            output = args.dbc.with_name(
                args.dbc.stem + "_patched" + args.dbc.suffix
            )

        new_header, new_records, added, replaced, skipped = write_dbc(
            args.dbc,
            output,
            mapping,
            args.replace,
            args.dry_run,
        )

        print(f"Source:            {args.dbc}")
        print(f"Requested IDs:     {len(mapping)}")
        print(f"Clone default:     {args.clone}")
        print(f"Added:             {len(added)}")
        print(f"Replaced:          {len(replaced)}")
        print(f"Skipped existing:  {len(skipped)}")

        if skipped:
            preview = ", ".join(map(str, skipped[:20]))
            if len(skipped) > 20:
                preview += ", ..."
            print(f"Skipped IDs:       {preview}")

        if args.dry_run:
            print("Dry run:           no file written")
        else:
            print(f"Output:            {output}")
            print(f"Output records:    {new_header.record_count}")
            print("Validation:        OK")

        return 0

    except (DBCError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
