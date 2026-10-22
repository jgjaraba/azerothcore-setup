#!/usr/bin/env python3
"""Strict name-table offset handling for ADT MMDX/MMID references."""
import struct


def name_offsets(body):
    result = {}
    pos = 0
    while pos < len(body):
        end = body.find(b'\0', pos)
        if end == -1:
            raise ValueError('Unterminated ADT model name')
        if end == pos:
            if any(body[pos:]):
                raise ValueError('Embedded empty ADT model name')
            break
        result[pos] = body[pos:end]
        pos = end + 1
    return result


def remap_name_table(old_body, new_body, offsets):
    """Keep MMID slot identities, including nonsequential/repeated references."""
    old, new = name_offsets(old_body), name_offsets(new_body)
    if len(old) != len(new) or len(offsets) % 4:
        raise ValueError('Model table shape changed or MMID is misaligned')
    mapping = dict(zip(old, new))
    result = bytearray()
    for (offset,) in struct.iter_unpack('<I', offsets):
        if offset not in mapping:
            raise ValueError(f'MMID offset {offset} is not a name start')
        result.extend(struct.pack('<I', mapping[offset]))
    return bytes(result)


def chunk(data, field, magic):
    if data[:12] != b'REVM\x04\0\0\0\x12\0\0\0' or data[12:16] != b'RDHM':
        raise ValueError('Unsupported ADT header')
    offset = struct.unpack_from('<I', data, 20 + field * 4)[0]
    if not offset:
        raise ValueError(f'Missing {magic!r}')
    pos = 20 + offset
    if pos + 8 > len(data) or data[pos:pos+4] != magic:
        raise ValueError(f'Invalid {magic!r} offset')
    size = struct.unpack_from('<I', data, pos+4)[0]
    if pos+8+size > len(data):
        raise ValueError(f'Truncated {magic!r}')
    return pos+8, data[pos+8:pos+8+size]


def placed_model_names(data):
    _, names = chunk(data, 3, b'XDMM')
    _, table = chunk(data, 4, b'DIMM')
    _, placements = chunk(data, 7, b'FDDM')
    starts = name_offsets(names)
    if len(table) % 4 or len(placements) % 36:
        raise ValueError('Misaligned model reference records')
    ids = [x[0] for x in struct.iter_unpack('<I', table)]
    if any(offset not in starts for offset in ids):
        raise ValueError('MMID references a non-start offset')
    resolved = []
    for i in range(0, len(placements), 36):
        index = struct.unpack_from('<I', placements, i)[0]
        if index >= len(ids):
            raise ValueError('MDDF references an invalid MMID index')
        resolved.append(starts[ids[index]])
    return resolved
