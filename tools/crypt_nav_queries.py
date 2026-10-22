#!/usr/bin/env python3
"""Select actual native navmesh samples, not invented averaged coordinates."""
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
import statistics

GROUPS = {18571:'exterior', 18699:'stairs', 18700:'wellroom',
          18701:'walk1', 18702:'walk2', 18703:'walk3', 18704:'walk4', 18705:'walk5',
          18706:'vault', 18810:'massgraves', 18811:'upsidedown', 18812:'sinkhole',
          18813:'underwater', 18814:'waterramp', 18815:'unrepentant',
          18818:'archedhall', 18819:'ossuary', 18820:'well', 18873:'collapsed'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--samples', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise ValueError('Output must be new')
    grouped = {}
    with args.samples.open() as f:
        for row in csv.DictReader(f, delimiter='\t'):
            group = int(row['group'])
            grouped.setdefault(group, []).append(tuple(float(row[k]) for k in ('x','y','z')))
    points = {'arrival': [-11068.1,-1806.4,52.85],
              'barrier_before': [-11068.088,-1825.5011,60.15711]}
    evidence = {}
    for group, xyz in grouped.items():
        if group not in GROUPS:
            raise ValueError('Unexpected crypt group')
        medians = [statistics.median(p[i] for p in xyz) for i in range(3)]
        point = min(xyz, key=lambda p: sum((p[i]-medians[i])**2 for i in range(3)))
        points[GROUPS[group]] = list(point)
        evidence[GROUPS[group]] = dict(group_id=group, samples=len(xyz), selected=list(point))
    args.output.mkdir(parents=True)
    report = dict(samples_sha256=hashlib.sha256(args.samples.read_bytes()).hexdigest(),
                  points=points, groups=evidence,
                  missing_group_samples=[GROUPS[g] for g in GROUPS if g not in grouped],
                  selection='Existing polygon centroid nearest XYZ medians, native WMO floor within1 unit')
    (args.output/'points.json').write_text(json.dumps(report,indent=2)+'\n')
    with (args.output/'queries.txt').open('w') as f:
        for a,b in itertools.permutations(points, 2):
            for mode in ('walk', 'swim'):
                f.write(f'{a}__{b}__{mode} ' + ' '.join(map(str,points[a]+list(points[b]))) + f' {mode}\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
