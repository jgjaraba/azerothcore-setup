#!/usr/bin/env python3
"""Summarize/compare native probe JSONL runs using identical point/query manifests."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', nargs='+', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    all_rows, summaries, reference = [], {}, None
    for path in args.runs:
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if any(row['type'] == 'error' for row in rows):
            raise ValueError(f'Probe execution failed: {path}')
        points = {row['id']: row for row in rows if row['type'] == 'point'}
        routes = [row for row in rows if row['type'] == 'route']
        signature = ({key: p['world'] for key, p in points.items()},
                     [(r['id'], r['from'], r['to'], r['mode']) for r in routes])
        if reference is not None and reference != signature:
            raise ValueError('Runs have different points/queries; refusing misleading comparison')
        reference = signature
        summary = dict(data=next(row['data'] for row in rows if row['type'] == 'metadata'),
                       mmap_tiles=sum(row['type'] == 'mmap_tile' for row in rows),
                       vmap_tiles=sum(row['type'] == 'vmap_tile' for row in rows),
                       points=len(points), routes=len(routes), rooms=len({p['room'] for p in points.values()}),
                       valid_floor=sum(p['vmap_floor'] is not None for p in points.values()), modes={})
        for mode in ('walk', 'swim'):
            subset = [r for r in routes if r['mode'] == mode]
            summary['modes'][mode] = dict(
                points_on_mesh=sum(p[mode]['valid'] for p in points.values()),
                queries=len(subset), complete=sum(r['complete'] for r in subset),
                endpoint_fail=sum(r.get('reason') == 'endpoint_not_on_tight_mesh' for r in subset),
                partial=sum(r.get('partial', False) for r in subset),
                out_of_nodes=sum(r.get('out_of_nodes', False) for r in subset),
                straight_within_mesh=sum(r.get('straight_within_mesh', False) for r in subset),
                los_clear=sum(r['los_feet_plus_1_5'] for r in subset))
        summary['rooms'] = {
            room: dict(points=sum(p['room'] == room for p in points.values()),
                       walk=sum(p['room'] == room and p['walk']['valid'] for p in points.values()),
                       swim=sum(p['room'] == room and p['swim']['valid'] for p in points.values()))
            for room in sorted({p['room'] for p in points.values()})}
        summaries[path.stem] = summary
        for r in routes:
            all_rows.append(dict(run=path.stem, id=r['id'], mode=r['mode'],
                                 from_room=r['from_room'], to_room=r['to_room'],
                                 complete=r['complete'], reason=r.get('reason', ''),
                                 los_clear=r['los_feet_plus_1_5'],
                                 straight_within_mesh=r.get('straight_within_mesh', ''),
                                 partial=r.get('partial', ''), out_of_nodes=r.get('out_of_nodes', ''),
                                 start_xy=r['start']['distance_xy'], start_z=r['start']['distance_z'],
                                 end_xy=r['end']['distance_xy'], end_z=r['end']['distance_z']))
    if all_rows:
        with (args.out / 'routes.csv').open('w', newline='') as output:
            writer = csv.DictWriter(output, fieldnames=list(all_rows[0]))
            writer.writeheader()
            writer.writerows(all_rows)
    (args.out / 'summary.json').write_text(json.dumps(summaries, indent=2)+'\n')
    print(json.dumps(summaries, indent=2))


if __name__ == '__main__':
    main()
