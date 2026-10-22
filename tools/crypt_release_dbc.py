"""Strict, lossless WDBC row transplant shared by release builders (stdlib only)."""
import struct


def parse_dbc(raw):
    if len(raw) < 20 or raw[:4] != b'WDBC':
        raise ValueError('Invalid WDBC header')
    count, fields, size, strings = struct.unpack_from('<4I', raw, 4)
    if not fields or size != fields * 4 or len(raw) != 20 + count * size + strings:
        raise ValueError('Invalid WDBC layout')
    rows = [list(struct.unpack_from(f'<{fields}I', raw, 20 + i * size))
            for i in range(count)]
    if len({r[0] for r in rows}) != count:
        raise ValueError('Duplicate DBC IDs')
    block = raw[20 + count * size:]
    if not block or block[0] != 0 or block[-1] != 0:
        raise ValueError('DBC string block must start and end with NUL')
    return fields, rows, block


def string_at(block, offset):
    if offset >= len(block):
        raise ValueError('Invalid DBC string offset')
    end = block.find(b'\0', offset)
    if end < 0:
        raise ValueError('Unterminated DBC string')
    return block[offset:end]


def semantic_row(row, block, string_fields):
    return tuple(string_at(block, value) if i in string_fields else value
                 for i, value in enumerate(row))


def merge_dbc(base: bytes, donor: bytes, ids: list[int],
              string_fields: list[int], order_map=False) -> bytes:
    """Transplant only ids; preserve base records/string prefix byte-for-byte.

    All fields are opaque uint32 bit patterns except explicitly named string
    offsets. Existing IDs must be semantically identical, regardless of offsets.
    Empty strings always map to offset zero. order_map stably orders by field 1
    (AreaTrigger's client search contract), rejecting an unsorted base.
    """
    fields, rows, strings = parse_dbc(base)
    donor_fields, source, source_strings = parse_dbc(donor)
    if fields != donor_fields:
        raise ValueError('DBC field count mismatch')
    if (len(set(ids)) != len(ids) or len(set(string_fields)) != len(string_fields)
            or any(i <= 0 or i >= fields for i in string_fields)):
        raise ValueError('Invalid IDs/string field declaration')
    if order_map and (fields < 2 or [r[1] for r in rows] != sorted(r[1] for r in rows)):
        raise ValueError('Base DBC is not ordered by map')
    # Validate every declared string offset, including opaque preserved rows.
    for records, block in ((rows, strings), (source, source_strings)):
        for row in records:
            for i in string_fields:
                string_at(block, row[i])
    existing, candidates = {r[0]: r for r in rows}, {r[0]: r for r in source}
    block = bytearray(strings)
    offsets = {b'': 0}
    changed = False
    for ident in ids:
        if ident not in candidates:
            raise ValueError(f'Missing donor ID {ident}')
        row = candidates[ident]
        if ident in existing:
            if semantic_row(existing[ident], strings, string_fields) != semantic_row(
                    row, source_strings, string_fields):
                raise ValueError(f'DBC ID collision: {ident}')
            continue
        copied = row.copy()
        for i in string_fields:
            text = string_at(source_strings, row[i])
            if text not in offsets:
                # Reuse existing strings, including suffix offsets, if possible.
                offset = block.find(text + b'\0')
                if offset < 0:
                    offset = len(block)
                    block.extend(text + b'\0')
                offsets[text] = offset
            copied[i] = offsets[text]
        rows.append(copied)
        changed = True
    if not changed:
        return base
    if order_map:
        rows.sort(key=lambda row: row[1])
    return (struct.pack('<4s4I', b'WDBC', len(rows), fields, fields * 4, len(block))
            + b''.join(struct.pack(f'<{fields}I', *row) for row in rows) + bytes(block))
