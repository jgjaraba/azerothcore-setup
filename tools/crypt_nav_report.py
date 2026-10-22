#!/usr/bin/env python3
"""Validate native query evidence, including explicit residual limitations."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from crypt_nav_generate import tile_info


def read(path):
    with path.open() as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    if len({r['label'] for r in rows}) != len(rows):
        raise ValueError('Duplicate query labels')
    return {r['label']:r for r in rows}


def summary(rows):
    complete = {k:r for k,r in rows.items() if r['complete'] == '1'}
    clean = {k:r for k,r in complete.items() if int(r['sampled_steps']) > 0
             and int(r['sampled_failed']) == 0 and int(r['sampled_vmap_blocked']) == 0}
    return dict(queries=len(rows), complete=len(complete), surface_and_vmap_pass=len(clean),
                partial_or_unreachable=len(rows)-len(complete),
                sampled_steps=sum(int(r['sampled_steps']) for r in complete.values()),
                height_edge_fallbacks=sum(int(r['height_edge_fallbacks']) for r in complete.values()),
                max_endpoint_snap=max(float(r['start_snap']) for r in complete.values()),
                long_corridors_over_148_polys=sum(int(r['polys']) > 148 for r in complete.values()))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--routes', type=Path, required=True)
    ap.add_argument('--baseline-routes', type=Path, required=True)
    ap.add_argument('--alternative-routes', type=Path, required=True)
    ap.add_argument('--controls', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise ValueError('Output must be new')
    rows, baseline, alternative, controls = map(read, (args.routes, args.baseline_routes,
                                                       args.alternative_routes, args.controls))
    if len(rows) != 760 or rows.keys() != baseline.keys() or rows.keys() != alternative.keys():
        raise ValueError('Query suite does not match')
    complete = {k for k,r in rows.items() if r['complete']=='1'}
    old_complete = {k for k,r in baseline.items() if r['complete']=='1'}
    alt_complete = {k for k,r in alternative.items() if r['complete']=='1'}
    if not old_complete <= complete or complete != alt_complete:
        raise ValueError('Candidate lost previously available point-pair connectivity')
    stats = summary(rows)
    if stats['complete'] != 350 or stats['surface_and_vmap_pass'] != 350:
        raise ValueError('Candidate native surface traversal failed')
    for r in rows.values():
        if not all(math.isfinite(float(r[k])) and float(r[k]) > -10000
                   for k in ('start_floor','end_floor')):
            raise ValueError('VMap floor validation did not load real geometry')
    expected = {'stacked_halls':('1','0'), 'stacked_well_ossuary':('0','0'),
                'stair_passage':('1','1'), 'wall_detour':('1','0')}
    for key,(route,los) in expected.items():
        r = controls[key]
        if (r['complete'],r['los']) != (route,los):
            raise ValueError('Native LOS/path control failed: '+key)
        if route == '1' and (int(r['sampled_failed']) or int(r['sampled_vmap_blocked'])):
            raise ValueError('Native surface/VMap control failed: '+key)
    if float(controls['stacked_halls']['length']) < 100:
        raise ValueError('Stacked floors joined by an incorrect shortcut')
    candidate = args.candidate/'mmaps'
    info = tile_info(candidate/'8005235.mmtile')
    if info['vertex_count'] >= 65535 or info['vertex_count'] != 54745:
        raise ValueError('Unexpected tile vertex count')
    root = Path(__file__).resolve().parent.parent
    native = root/'work/server-data/crypt-refs-r2/mmaps'
    preserved = []
    for p in sorted(native.glob('800*')):
        if p.read_bytes() != (candidate/p.name).read_bytes():
            raise ValueError('Unchanged pilot map/tile differs: '+p.name)
        preserved.append(p.name)
    if len(preserved) != 6:
        raise ValueError('Expected five original tiles plus map params')
    log = (args.candidate/'generator.log').read_text().lower()
    if log.count('writing to file') != 6 or any(word in log for word in ('too many','failed','error')):
        raise ValueError('Generator had incomplete/error output')
    report = dict(candidate=stats, baseline=summary(baseline), alternative=summary(alternative),
                  new_tile=info, six_existing_files_byte_identical=preserved,
                  controls=controls,
                  evidence_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in (args.routes,args.baseline_routes,args.alternative_routes,args.controls)},
                  in_game_validated=False,
                  limitations=[
                      '410 diagnostic point-pair/filter combinations remain partial or disconnected.',
                      'Group18820 (well) has no selected ground-navmesh sample.',
                      'Native offline Detour/VMap queries are not live Unit/PathGenerator execution.',
                      'Dense 0.4-unit surface sampling uses larger diagnostic buffers than Unit movement.',
                      'Body-height LOS segments do not validate a swept collision capsule or dynamic objects.',
                      'Water/vertical transitions and disconnected rooms require separate inspection; no forced offmesh links added.'])
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('controls','evidence_sha256')},indent=2))


if __name__ == '__main__':
    main()
