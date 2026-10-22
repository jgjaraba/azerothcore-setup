#!/usr/bin/env python3
"""Derive pinned WORLD floor POIs from revision-1 WMO triangles and native VMap measurements.

No runtime or /tmp input. Selection uses collision floors/group IDs, never Detour success.
Writes seeds, native measurements, points, queries and provenance beneath --out.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess

from crypt_collision_fix import group, records

ROOT = Path(__file__).resolve().parents[1]
# Target group index, native WMO group ID and research name (group-remap.json).
GROUPS = [
    (0, 18699, 'stairs'), (1, 18700, 'wellroom'), (2, 18702, 'wonkyhall02'),
    (3, 18703, 'wonkyhall03'), (4, 18704, 'wonkyhall04'), (5, 18705, 'wonkyhall05'),
    (6, 18706, 'dozenVaultroom'), (7, 18571, 'exterior'), (8, 18810, 'massgraves'),
    (9, 18811, 'upsidedownhell'), (10, 18812, 'theSinkhole'), (11, 18813, 'underwaterarches'),
    (12, 18814, 'water_ramp'), (13, 18815, 'unfinished'), (14, 18818, 'arched_hallway'),
    (15, 18819, 'ossuary'), (16, 18820, 'well'), (17, 18873, 'collapsedRoom'),
    (18, 18701, 'wonkyhall01'),
]
POINT_HEADER = ['id', 'room', 'x', 'y', 'z']
QUERY_HEADER = ['id', 'from', 'to', 'mode']


def write_csv(path, header, rows):
    with path.open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_label(path):
    return str(path.resolve().relative_to(ROOT)) if path.resolve().is_relative_to(ROOT) else str(path.resolve())


def placement(revision):
    found = set()
    sources = {}
    for path in sorted((revision / 'payload/World/Maps/KarazhanCrypt').glob('*.adt')):
        data = path.read_bytes()
        offset, parts = 0, {}
        while offset < len(data):
            tag, size = struct.unpack_from('<4sI', data, offset)
            if offset + 8 + size > len(data):
                raise ValueError(f'Truncated ADT: {path}')
            if tag in (b'FDOM', b'OMWM', b'DIWM'):
                parts[tag] = data[offset+8:offset+8+size]
            offset += 8 + size
        for row in records(parts.get(b'FDOM', b''), '<II12f4H'):
            if row[1] == 571057:
                name_offset = struct.unpack_from('<I', parts[b'DIWM'], row[0]*4)[0]
                name = parts[b'OMWM'][name_offset:].split(b'\0')[0].decode()
                if name.lower().replace('\\', '/') != 'world/wmo/custom/turtle800/tw800crypt.wmo':
                    raise ValueError(f'Unexpected spawn model: {name}')
                found.add((0, *row[1:]))  # Per-ADT name-table index is not placement identity.
                sources[source_label(path)] = digest(path)
    if len(found) != 1:
        raise ValueError(f'Expected one consistent MODF 571057; got {found}')
    row = found.pop()
    # MODF file axes -> native ModelSpawn axes, as in vmap4_extractor.
    position = (row[4], row[2], row[3])
    rotation = tuple(row[5:8])
    if abs(rotation[0]) > 1e-5 or abs(rotation[2]) > 1e-5:
        raise ValueError(f'Unexpected tilted WMO: {rotation}')
    theta = math.radians(rotation[1])
    c, s = math.cos(theta), math.sin(theta)
    # These values also reproduce crypt_probe.py's local/world ray evidence.
    def world(p):
        mid = 17066.666666666668
        return (mid-position[0]-c*p[0]+s*p[1],
                mid-position[1]-s*p[0]-c*p[1], position[2]+p[2])
    return world, dict(spawn_id=571057, modf=list(row), native_position=position,
                       native_rotation=rotation, source_adts=sources)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT / 'work/server-data/crypt-refs-r2')
    parser.add_argument('--revision', type=Path, default=ROOT / 'work/crypt-fix/revision-1')
    parser.add_argument('--out', type=Path, default=ROOT / 'work/crypt-nav-probe')
    parser.add_argument('--probe', type=Path, default=ROOT / 'work/crypt-nav-probe/bin/crypt_nav_probe')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    world, provenance = placement(args.revision)
    seeds = []
    source = {}
    metadata = {}
    for index, group_id, room in GROUPS:
        path = args.revision / f'wmo/World/wmo/Custom/Turtle800/tw800crypt_{index:03}.wmo'
        source[source_label(path)] = digest(path)
        _, head, parts = group(path.read_bytes())
        actual_id = struct.unpack_from('<I', head, 56)[0]
        if actual_id != group_id:
            raise ValueError(f'Unexpected group ID: {path}: {actual_id} != {group_id}')
        vertices = records(parts['MOVT'], '<3f')
        candidates = []
        for tri_id, indices in enumerate(records(parts['MOVI'], '<3H')):
            a, b, c = [vertices[i] for i in indices]
            u, v = [b[k]-a[k] for k in range(3)], [c[k]-a[k] for k in range(3)]
            normal = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
            area = math.sqrt(sum(n*n for n in normal))
            # Broad surface candidates; VMap decides whether they really are floors.
            if area < 1 or abs(normal[2]) / area < .75:
                continue
            p = tuple((a[k]+b[k]+c[k])/3 for k in range(3))
            candidates.append((tri_id, p))
        # Deterministic spatial coverage, not triangle-order bias. Keep up to 100/group.
        chosen = []
        candidates.sort(key=lambda item: (item[1][2], item[0]))
        if candidates:
            chosen.append(candidates.pop(0))
        while candidates and len(chosen) < 100:
            best = max(candidates, key=lambda item: min(math.dist(item[1], p) for _, p in chosen))
            chosen.append(best)
            candidates.remove(best)
        for tri_id, local in chosen:
            name = f'{room}_tri{tri_id}'
            p = world(local)
            # Search from 0.75 above the actual source surface, not the WMO bounding-box roof.
            seeds.append([name, room, *p[:2], p[2]+.75])
            metadata[name] = dict(group_index=index, group_id=group_id, room=room,
                                  triangle=tri_id, local=list(local), source_world=list(p))
    write_csv(args.out / 'floor-seeds.csv', POINT_HEADER, seeds)
    write_csv(args.out / 'empty-queries.csv', QUERY_HEADER, [])
    command = [str(args.probe), '--data', str(args.data), '--points', str(args.out / 'floor-seeds.csv'),
               '--queries', str(args.out / 'empty-queries.csv'), '--floor-search', '2']
    with (args.out / 'floor-measurements.jsonl').open('w') as output:
        subprocess.run(command, stdout=output, check=True)
    measured = [json.loads(line) for line in (args.out / 'floor-measurements.jsonl').read_text().splitlines()]
    points, selected, missing = [], {}, []
    for _, group_id, room in GROUPS:
        usable = []
        for row in measured:
            if row['type'] != 'point' or row['room'] != room:
                continue
            area = row['vmap_area']
            floor = row['vmap_floor']
            if (floor is None or not area or area['group_id'] != group_id
                    or area['model'].lower() != 'tw800crypt.wmo'
                    or math.dist(area['native_position'], provenance['native_position']) > .01
                    or math.dist(area['native_rotation'], provenance['native_rotation']) > .01
                    or abs(floor-metadata[row['id']]['source_world'][2]) > .35):
                continue
            usable.append(row)
        if not usable:
            missing.append(room)
            continue
        # Low, distant, third distant point; no filtering by walk/swim snap or path results.
        chosen = [min(usable, key=lambda row: (row['vmap_floor'], row['id']))]
        usable.remove(chosen[0])
        while usable and len(chosen) < 3:
            best = max(usable, key=lambda row: min(math.dist(row['world'], p['world']) for p in chosen))
            if min(math.dist(best['world'], p['world']) for p in chosen) < 1:
                break
            chosen.append(best)
            usable.remove(best)
        selected[room] = []
        for i, row in enumerate(chosen):
            name = f'{room}_{i+1}'
            points.append([name, room, *row['world'][:2], row['vmap_floor']+.2])
            selected[room].append(dict(id=name, world=points[-1][2:], vmap_floor=row['vmap_floor'],
                                       seed=metadata[row['id']], measured_area=row['vmap_area']))
    write_csv(args.out / 'points.csv', POINT_HEADER, points)
    queries = []
    def pair(label, a, b):
        for mode in ('walk', 'swim'):
            queries.append([f'{label}_{mode}', a, b, mode])
    for room, rows in selected.items():
        if len(rows) > 1:
            pair(room+'_panel', rows[0]['id'], rows[1]['id'])
        if len(rows) > 2:
            pair(room+'_panel2', rows[1]['id'], rows[2]['id'])
    # Cross-room panels are measurements, not assertions of intended walkable connectivity.
    links = [('stairs', 'wellroom'), ('wellroom', 'wonkyhall01'), ('wonkyhall01', 'wonkyhall02'),
             ('wonkyhall02', 'dozenVaultroom'), ('wonkyhall02', 'wonkyhall03'),
             ('wonkyhall04', 'wonkyhall05'), ('wonkyhall05', 'massgraves'),
             ('massgraves', 'upsidedownhell'), ('upsidedownhell', 'theSinkhole'),
             ('upsidedownhell', 'underwaterarches'), ('underwaterarches', 'water_ramp'),
             ('water_ramp', 'arched_hallway'), ('arched_hallway', 'ossuary'),
             ('wellroom', 'well'), ('well', 'ossuary'), ('unfinished', 'collapsedRoom'),
             ('exterior', 'stairs')]
    for a, b in links:
        if a in selected and b in selected:
            pair(a+'_to_'+b, selected[a][0]['id'], selected[b][0]['id'])
    write_csv(args.out / 'queries.csv', QUERY_HEADER, queries)
    provenance.update(source_wmos=source, groups=GROUPS, selected=selected, missing_floor_groups=missing,
                      selection='native floor <=0.35 from WMO surface; group+model+placement match; no Detour selection',
                      points_sha256=digest(args.out / 'points.csv'), queries_sha256=digest(args.out / 'queries.csv'))
    (args.out / 'manifest.json').write_text(json.dumps(provenance, indent=2)+'\n')
    print(json.dumps(dict(points=len(points), queries=len(queries), missing_floor_groups=missing)))


if __name__ == '__main__':
    main()
