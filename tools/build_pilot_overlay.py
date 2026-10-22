#!/usr/bin/env python3
"""Build a copy-only, revision-1 map-800 priority overlay; never install it.

Requires tools/mpq built from mpq.cpp with StormLib. Unknown inputs fail closed.
The only payload mutation besides removing obsolete map-800 terrain is replacing
the conflicting Map.dbc row 800, retaining every other row and the string block.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
T = "Data/patch-T.MPQ"
ZS = ("Data/patch-Z.mpq", "Data/esES/patch-esES-Z.MPQ")
KNOWN = {
    T: "1455f5576b11c8ea53187488643f37970ec1798ce07483cdebf4c962d57f5229",
    ZS[0]: "702b6d03ae842fb8b1af79693ccef5747863730e1245cabe8c896072efd9e74e",
    ZS[1]: "05e923addefaf14d1c813d0a77cff2f6ba3d04fb3a5f25f5110cd6fb8c0ac631",
}
PREFIX = "world\\maps\\karazhancrypt\\"
DBC = "DBFilesClient\\Map.dbc"
SCHEMAS = {
    "Map": (66, {1, *range(5, 21), *range(23, 39), *range(40, 56)}),
    "AreaTable": (36, set(range(11, 27))),
    "MapDifficulty": (23, set(range(3, 19))),
}
TERRAIN = {PREFIX + "karazhancrypt.wdt"} | {
    PREFIX + f"karazhancrypt_{x}_{y}.adt" for x in (34, 35, 36) for y in (52, 53)
}
OBSOLETE = PREFIX + "karachancrypt.wdl"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(mpq, *args):
    return subprocess.run([str(mpq), *map(str, args)], check=True,
                          capture_output=True, text=True)


def listing(mpq, archive):
    result = run(mpq, "list", archive)
    entries = {}
    for line in result.stdout.splitlines():
        name, size = line.rsplit("\t", 1)
        key = name.lower()
        require(key not in entries, f"Duplicate/case alias: {name}")
        require(not re.fullmatch(r"file[0-9a-f]+\..*", key),
                f"Unresolved listfile name: {name}")
        require("/" not in name and not any(c in name for c in "\r\n"),
                f"Unsupported name: {name!r}")
        entries[key] = {"name": name, "size": int(size)}
    count = re.search(r"^# archive files: (\d+)$", result.stderr, re.M)
    require(count and int(count[1]) == len(entries),
            f"Incomplete enumeration or old mpq binary: {archive}")
    require("(listfile)" in entries, f"Missing internal listfile: {archive}")
    return entries


def extract(mpq, archive, entry, temp):
    path = temp / "entry"
    path.unlink(missing_ok=True)
    run(mpq, "extract-one", archive, entry["name"], path)
    data = path.read_bytes()
    require(len(data) == entry["size"], f"Short extraction: {entry['name']}")
    return data


def inventory(mpq, archive, temp):
    entries = listing(mpq, archive)
    for entry in entries.values():
        entry["sha256"] = digest(extract(mpq, archive, entry, temp))
    lf = extract(mpq, archive, entries["(listfile)"], temp).decode("utf-8")
    names = [name.lower() for name in lf.splitlines() if name]
    require(len(names) == len(set(names)), "Duplicate listfile entries")
    require(set(names) - {"(listfile)", "(attributes)", "(signature)"}
            == set(entries) - {"(listfile)", "(attributes)", "(signature)"},
            f"Incomplete/stale internal listfile: {archive}")
    return entries


def parse_dbc(data, kind):
    fields, string_cols = SCHEMAS[kind]
    require(len(data) >= 20 and data[:4] == b"WDBC", f"Invalid {kind} magic")
    count, fc, size, strings_size = struct.unpack_from("<4I", data, 4)
    require(fc == fields and size == fields * 4
            and len(data) == 20 + count * size + strings_size,
            f"Unknown {kind} layout")
    strings = data[20 + count * size:]
    require(strings and strings[0] == 0 and strings[-1] == 0,
            f"Invalid {kind} string block")
    rows = [struct.unpack_from(f"<{fc}I", data, 20 + i * size) for i in range(count)]
    require(len({r[0] for r in rows}) == count, f"Duplicate {kind} IDs")

    def text(offset):
        require(offset < len(strings), f"Invalid {kind} string offset")
        end = strings.find(b"\0", offset)
        require(end >= offset, f"Unterminated {kind} string")
        return strings[offset:end]

    semantic = {row[0]: [text(v).decode("utf-8") if col in string_cols else v
                          for col, v in enumerate(row)] for row in rows}
    return rows, strings, semantic


def merge_map(source, pilot):
    rows, strings, before = parse_dbc(source, "Map")
    pilot_rows, pilot_strings, desired = parse_dbc(pilot, "Map")
    require(800 in before and desired.get(800, [None, None])[1] == "KarazhanCrypt",
            "Missing/unknown map 800")
    require(before[800][1] == "KarazhanCrypt" and desired[800][2] == 1,
            "Map 800 contract mismatch")
    new_row = list(next(row for row in pilot_rows if row[0] == 800))
    sb = bytearray(strings)
    for col in SCHEMAS["Map"][1]:
        offset = new_row[col]
        end = pilot_strings.index(0, offset)
        value = pilot_strings[offset:end]
        new_row[col] = len(sb) if value else 0
        if value:
            sb.extend(value + b"\0")
    replacement = [new_row if row[0] == 800 else row for row in rows]
    merged = (struct.pack("<4s4I", b"WDBC", len(rows), 66, 264, len(sb))
              + b"".join(struct.pack("<66I", *r) for r in replacement) + sb)
    after_rows, after_strings, after = parse_dbc(merged, "Map")
    require(after[800] == desired[800], "Pilot row semantic mismatch")
    require([r for r in rows if r[0] != 800]
            == [r for r in after_rows if r[0] != 800]
            and after_strings.startswith(strings), "Non-pilot DBC bytes changed")
    require(all(after[k] == v for k, v in before.items() if k != 800),
            "Non-pilot DBC semantics changed")
    return merged, {"action": "replace_only_row_800", "before_row": before[800],
                    "after_row": after[800], "non_pilot_rows_preserved": len(rows) - 1,
                    "original_string_block_preserved": True}


def build(args):
    source, output, mpq = args.source.resolve(), args.output.absolute(), args.mpq.resolve()
    require(not output.exists() and not output.is_symlink(), "Output already exists")
    require(source not in output.resolve().parents and output.resolve() != source,
            "Output must be outside the source client")
    for rel in KNOWN:
        require(not (source / rel).is_symlink(), f"Symlink source: {rel}")
    before = {rel: sha(source / rel) for rel in KNOWN}
    require(before == KNOWN, f"Unknown revision/source changed: {before}")
    research = json.loads(args.audit.read_text())
    audited = {a["path"]: a for a in research["archives"]}
    require(research["root"] == str(source), "Audit source mismatch")
    for rel in KNOWN:
        require(audited.get(str(source / rel), {}).get("sha256") == KNOWN[rel],
                f"Audit version mismatch: {rel}")
    report = {"status": "building", "revision": "crypt-fix-revision-1", "map": 800,
              "source": str(source), "source_sha256_before": before,
              "audit_sha256": sha(args.audit), "archives": {},
              "exceptions": ["(listfile): regenerated membership metadata",
                             "DBFilesClient\\Map.dbc: only row 800 and appended strings"],
              "installed": False}
    # Read/validate everything before creating a package directory.
    with tempfile.TemporaryDirectory(prefix="pilot-overlay-") as directory:
        temp = Path(directory)
        inventories = {rel: inventory(mpq, source / rel, temp) for rel in KNOWN}
        pilot = inventories[T]
        require({k for k in pilot if k.startswith(PREFIX)} == TERRAIN,
                "Unknown pilot terrain inventory")
        pilot_dbc = {}
        for kind in SCHEMAS:
            key = f"dbfilesclient\\{kind.lower()}.dbc"
            pilot_dbc[kind] = extract(mpq, source / T, pilot[key], temp)
            parse_dbc(pilot_dbc[kind], kind)
        plans = {}
        for rel in ZS:
            entries = inventories[rel]
            removed = {k for k in entries if k.startswith(PREFIX)}
            require(removed == TERRAIN | {OBSOLETE}, f"Unknown map terrain: {rel}")
            expected = {e["name"].lower(): e["sha256"]
                        for e in audited[str(source / rel)]["entries"]}
            require({k: entries[k]["sha256"] for k in removed} == expected,
                    f"Terrain differs from audited map 800: {rel}")
            audits = {}
            merged_map = None
            for kind in SCHEMAS:
                key = f"dbfilesclient\\{kind.lower()}.dbc"
                if key not in entries:
                    audits[kind] = {"action": "absent_no_override"}
                    continue
                data = extract(mpq, source / rel, entries[key], temp)
                if kind == "Map":
                    merged_map, audits[kind] = merge_map(data, pilot_dbc[kind])
                else:
                    # Other DBC layouts in Z are not part of the known revision.
                    # Never silently drop a table or accept a new collision.
                    parse_dbc(data, kind)
                    raise ValueError(f"Unexpected {kind} override in {rel}; needs record-level analysis")
            require(merged_map is not None, f"Known Map.dbc missing in {rel}")
            plans[rel] = (removed, merged_map, audits)
        require({rel: sha(source / rel) for rel in KNOWN} == before,
                "Source changed during preflight")
        output.mkdir(parents=True, exist_ok=False)
        try:
            for rel in KNOWN:
                dest = output / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source / rel, dest)
                require(sha(dest) == before[rel], f"Copy mismatch: {rel}")
                if rel in ZS:
                    backup = output / "originals" / rel
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(dest, backup)
                    require(sha(backup) == before[rel], f"Backup mismatch: {rel}")
                    removed, merged, audits = plans[rel]
                    run(mpq, "remove", dest,
                        *[inventories[rel][k]["name"] for k in sorted(removed)])
                    dbc_path = temp / "Map.dbc"
                    dbc_path.write_bytes(merged)
                    run(mpq, "add", dest, dbc_path, DBC)
                else:
                    removed, audits = set(), {}
                after = inventory(mpq, dest, temp)
                original = inventories[rel]
                require(set(after) == set(original) - removed,
                        f"Unexpected added/deleted files: {rel}")
                preserved = []
                changed = []
                for key in sorted(after):
                    old, new = original[key], after[key]
                    item = {"name": old["name"], "source_sha256": old["sha256"],
                            "output_sha256": new["sha256"], "source_size": old["size"],
                            "output_size": new["size"]}
                    if old["sha256"] == new["sha256"]:
                        preserved.append(item)
                    else:
                        require(rel in ZS and key in {"(listfile)", DBC.lower()},
                                f"Changed file outside map 800: {rel}: {key}")
                        if key == DBC.lower():
                            require(extract(mpq, dest, new, temp) == plans[rel][1],
                                    "Unexpected DBC mutation")
                        changed.append(item)
                report["archives"][rel] = {
                    "source_sha256": before[rel], "output_sha256": sha(dest),
                    "removed": [{**original[k], "source_sha256": original[k]["sha256"],
                                 "output_sha256": None, "reason": "obsolete WDL" if k == OBSOLETE
                                 else "pilot owns terrain"} for k in sorted(removed)],
                    "preserved_entries": preserved, "changed_entries": changed,
                    "dbc_audit": audits, "listfile_complete": True,
                }
            report["source_sha256_after"] = {rel: sha(source / rel) for rel in KNOWN}
            require(report["source_sha256_after"] == before, "Source changed during build")
            require(sha(output / T) == KNOWN[T], "Pilot must be byte-identical")
            for rel in ZS:
                require(sha(output / "originals" / rel) == KNOWN[rel], "Backup changed")
                require(not any(k.startswith(PREFIX) for k in listing(mpq, output / rel)),
                        "Z still owns map-800 terrain")
            (output / "INSTALL.md").write_text(installation_notes())
            report["status"] = "verified"
        except Exception as error:
            report["status"] = "failed_do_not_install"
            report["error"] = str(error)
            raise
        finally:
            (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(output), "status": report["status"],
                      "sha256": {rel: a["output_sha256"]
                                 for rel, a in report["archives"].items()}}, indent=2))


def installation_notes():
    return """# Overlay map 800 — revision 1

Built and verified on copies only. No client was installed or modified.
`report.json` must say `verified`. Data contains the three installable archives
at their exact original, case-sensitive paths. T is byte-identical revision 1.
Both Z copies have seven overlapping terrain files and one stale WDL removed.
Map.dbc is retained: only row 800 is replaced with T's row, strings appended;
all non-800 rows remain byte-identical. T uniquely owns map-800 terrain/WMO;
the later Z Map.dbc tables must retain the compatible row 800 (DBC tables are
whole-file overrides, not merged by the client).

## Manual installation on the intended client, with the game stopped

Do not run these instructions against the original research snapshots.
Set PACKAGE to this package directory and CLIENT to the intended install copy.
Use a NEW BACKUP directory OUTSIDE CLIENT/Data. Before installation, check that
the existing Z archives match `source_sha256` in report.json; check any existing
T matches revision 1. Abort on any mismatch. Preserve filename case exactly.

1. Move CLIENT/Data/patch-Z.mpq to BACKUP/Data/patch-Z.mpq.
2. Move CLIENT/Data/esES/patch-esES-Z.MPQ to BACKUP/Data/esES/patch-esES-Z.MPQ.
3. If T already exists, move CLIENT/Data/patch-T.MPQ to BACKUP/Data/patch-T.MPQ;
   otherwise record that it was absent.
4. Copy the three files from PACKAGE/Data to the same relative paths in CLIENT.
5. Check all three installed SHA-256 against `output_sha256` in report.json.
   If any operation fails, restore the backups before starting the game.

Never keep renamed original MPQs anywhere inside Data (including locale dirs).
`originals/` in this package holds byte-identical source Z backups outside Data;
keep the complete package outside the client Data directory as well.

## Rollback

Stop the game. Remove the three installed overlay archives. Move each archive
from BACKUP back to its exact original path. If T was originally absent, leave
it absent. Check restored hashes against the pre-installation hashes. Do not
restore just Z while leaving the pilot active: that recreates the old conflict.

Structural/content verification does not establish in-game traversal.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("/home/dev/wow-335"))
    parser.add_argument("--output", type=Path, default=ROOT / "work/client-overlay-r1")
    parser.add_argument("--mpq", type=Path, default=ROOT / "tools/mpq")
    parser.add_argument("--audit", type=Path,
                        default=Path("/tmp/opencode/crypt-snapshot-audit/report.json"))
    args = parser.parse_args()
    try:
        build(args)
    except (ValueError, OSError, subprocess.CalledProcessError, KeyError) as error:
        parser.exit(1, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
