#!/usr/bin/env python3
"""Stage map-800 coordinate metadata, preserving the server's own DBC baseline.

Does not install or restart anything. Uses the project's local DEV login path
only for a read-only SQL overlay collision check.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess

from build_crypt_cartography import dbc, require
from dbc_write import write_dbc_bytes


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--server', type=Path, required=True)
    ap.add_argument('--client', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    require(not args.output.exists(), 'Output must be a new directory')
    server_data, client_data = args.server.read_bytes(), args.client.read_bytes()
    _, rows, strings = dbc(server_data, 11)
    _, client_rows, client_strings = dbc(client_data, 11)
    candidates = [r for r in client_rows if r[0:3] == [674, 800, 5086]]
    require(len(candidates) == 1, 'Expected the validated pilot row')
    require(len({r[0] for r in rows}) == len(rows), 'Duplicate server row IDs')
    require(not any(r[0] == 674 or r[1] == 800 or r[2] == 5086 for r in rows),
            'Server DBC collision')
    row = candidates[0].copy()
    require(0 <= row[3] < len(client_strings), 'Client name offset out of range')
    require(row[3] == 0 or client_strings[row[3]-1] == 0,
            'Client name offset is not a string start')
    bounds = struct.unpack('<4f', struct.pack('<4I', *row[4:8]))
    require(all(math.isfinite(v) for v in bounds) and bounds[0] != bounds[1]
            and bounds[2] != bounds[3], 'Invalid world-map bounds')
    require(row[8:] == [0xffffffff, 0, 0], 'Unexpected world-map routing metadata')
    end = client_strings.find(b'\0', row[3])
    require(end >= row[3], 'Invalid client string')
    name = client_strings[row[3]:end]
    require(name == b'KarazhanCrypt', 'Unexpected map name')
    sql = subprocess.run([
        'mysql', '--login-path=azeroth-dev', '-N', '-B', 'acore_world', '-e',
        'SELECT ID FROM worldmaparea_dbc WHERE ID=674 OR MapID=800 OR AreaID=5086'
    ], check=True, capture_output=True)
    require(not sql.stdout.strip(), 'SQL overlay collision')
    row[3] = len(strings)
    result = write_dbc_bytes(11, rows + [row], strings + name + b'\0')
    require(result[20:20+44*len(rows)] == server_data[20:20+44*len(rows)],
            'Original server rows changed')
    _, new_rows, new_strings = dbc(result, 11)
    require(new_rows[:-1] == rows and new_strings[:len(strings)] == strings,
            'Server baseline was not preserved')
    # Same geographic metadata, independently allocated string offsets.
    require(row[:3] + row[4:] == candidates[0][:3] + candidates[0][4:],
            'Client/server metadata mismatch')
    require(args.server.read_bytes() == server_data, 'Server input changed')
    args.output.mkdir(parents=True)
    (args.output / 'WorldMapArea.before.dbc').write_bytes(server_data)
    (args.output / 'WorldMapArea.dbc').write_bytes(result)
    report = dict(rows_before=len(rows), rows_after=len(new_rows),
                  source_sha256=sha(server_data), output_sha256=sha(result),
                  row_id=674, map_id=800, area_id=5086,
                  existing_rows_and_strings_preserved=True,
                  sql_collision_check='no matching rows')
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
