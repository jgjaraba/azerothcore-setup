#!/usr/bin/env python3
"""Minimal WDBC reader for the turtle-wow-maps port (3.3.5a / 1.12.1).

Usage:
  dbc.py dump <file.dbc> [--limit N] [--cols 0,1,2]
  dbc.py schema <file.dbc>
"""
import struct, sys

def read_dbc(path):
    with open(path, 'rb') as f:
        data = f.read()
    magic = data[:4]
    if magic == b'WDBC':
        (rec_count, field_count, rec_size, str_size) = struct.unpack_from('<4I', data, 4)
        header = 20
    elif magic == b'WDB2' or magic == b'WDB3':
        raise SystemExit('WDB2/WDB3 not supported yet')
    else:
        raise SystemExit('unknown magic %r' % magic)
    records_data = data[header:header + rec_count * rec_size]
    string_block = data[header + rec_count * rec_size: header + rec_count * rec_size + str_size]
    records = []
    for i in range(rec_count):
        rec = struct.unpack_from('<%dI' % field_count, records_data, i * rec_size)
        records.append(rec)
    def get_string(off):
        if off == 0 or off >= len(string_block):
            return ''
        end = string_block.find(b'\x00', off)
        if end == -1:
            end = len(string_block)
        return string_block[off:end].decode('latin1', errors='replace')
    return field_count, records, get_string

def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return
    cmd = args[0]
    path = args[1]
    fc, records, get_string = read_dbc(path)
    if cmd == 'schema':
        print('fields=%d records=%d' % (fc, len(records)))
        return
    if cmd == 'dump':
        limit = None
        cols = None
        i = 2
        while i < len(args):
            if args[i] == '--limit':
                limit = int(args[i+1]); i += 2
            elif args[i] == '--cols':
                cols = [int(x) for x in args[i+1].split(',')]; i += 2
            else:
                i += 1
        for idx, rec in enumerate(records):
            if limit is not None and idx >= limit:
                break
            vals = []
            for j, v in enumerate(rec):
                if cols is not None and j not in cols:
                    continue
                vals.append(str(v))
            print(idx, '\t'.join(vals))
    else:
        print('unknown cmd', cmd)

if __name__ == '__main__':
    main()
