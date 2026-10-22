#!/usr/bin/env python3
"""Generic WDBC read/write helpers for the DBC merge step."""
import struct

def read_dbc_bytes(data):
    assert data[:4] == b'WDBC', 'not WDBC'
    rec_count, field_count, rec_size, str_size = struct.unpack_from('<4I', data, 4)
    header = 20
    records = []
    for i in range(rec_count):
        rec = struct.unpack_from('<%dI' % field_count, data, header + i * rec_size)
        records.append(list(rec))
    string_block = data[header + rec_count * rec_size: header + rec_count * rec_size + str_size]
    return field_count, records, string_block

def write_dbc_bytes(field_count, records, string_block):
    rec_count = len(records)
    rec_size = field_count * 4
    out = bytearray()
    out += b'WDBC'
    out += struct.pack('<4I', rec_count, field_count, rec_size, len(string_block))
    for rec in records:
        assert len(rec) == field_count, f'row has {len(rec)} fields, need {field_count}'
        for v in rec:
            out += struct.pack('<I', v)
    out += string_block
    return bytes(out)

def add_string(string_block, s):
    """Append a NUL-terminated string, return its offset in the (new) block."""
    off = len(string_block)
    string_block += s.encode('utf-8', errors='replace') + b'\x00'
    return off

def read_dbc_file(path):
    with open(path, 'rb') as f:
        return read_dbc_bytes(f.read())

def write_dbc_file(path, field_count, records, string_block):
    with open(path, 'wb') as f:
        f.write(write_dbc_bytes(field_count, records, string_block))
