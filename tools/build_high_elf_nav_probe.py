#!/usr/bin/env python3
"""Build/run read-only Map0 queries using existing AC objects and libraries.

No CMake, core compilation, database connection or server lifecycle operations.
Reuses the crypt probe's common includes and mmaps_generator link recipe.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import shlex
import struct
import subprocess

from adt import _adt_layout

ROOT = Path(__file__).resolve().parent.parent
CORE = Path('/home/dev/azerothcore')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(out):
    def rows(name):
        with (out / name).open() as stream:
            return list(csv.DictReader(stream, delimiter='\t'))

    evidence = json.loads((out / 'evidence.json').read_text())
    paths, rays, teleports = rows('paths.tsv'), rows('rays.tsv'), rows('teleports.tsv')
    loads, samples = rows('loads.tsv'), rows('samples.tsv')
    modes = {}
    for mode in sorted({row['mode'] for row in paths}):
        subset = [row for row in paths if row['mode'] == mode]
        modes[mode] = dict(queries=len(subset), complete=sum(row['complete'] == '1' for row in subset),
                           outcomes=dict(Counter(row['path_status_text'] for row in subset)),
                           missing_endpoint=sum(row['reason'] in ('missing_endpoint_poly', 'no_same_floor_destination')
                                                for row in subset))
    result = dict(loads=dict(Counter(row['kind'] for row in loads)), samples=len(samples), modes=modes,
                  unique_loaded_models=evidence['native_loaded_unique_models_manifest_verified'],
                  loaded_model_instances=evidence['native_loaded_model_instances'],
                  absent_halo_maps=evidence['absent_halo_maps'],
                  source_areas=sorted({int(row['area']) for row in samples}),
                  rays=dict(total=len(rays), hits=sum(row['hit'] == '1' for row in rays),
                            blocked=sum(row['los'] == '0' for row in rays),
                            roots=dict(Counter(row['root'] for row in rays))),
                  inn_queries=[row for row in paths if row['label'].startswith('inn_')],
                  cross_region=[row for row in paths if '_to_' in row['label'] and not row['label'].startswith('inn_')],
                  teleports=teleports,
                  limits=['Offline Detour corridors, not live Unit movement or gameplay.',
                          'Path completion and direct static VMap LoS are independent results.',
                          'Partial results and OUT_OF_NODES do not prove disconnected geography.',
                          'Water-only uses NAV_WATER; walk_swim uses NAV_GROUND|NAV_WATER.',
                          'Missing water samples are reported in run.log, not fabricated.',
                          'No dynamic GameObject collision, client rendering or in-game validation.'])
    if result['loads'].get('mmap') != 522 or result['loads'].get('vmap') != 374:
        raise ValueError('Native loaded set is incomplete')
    if {int(row['area']) for row in teleports} != {2040, 5533}:
        raise ValueError('Could not establish both offline teleport candidates')
    if not result['inn_queries'] or not result['rays']['hits']:
        raise ValueError('Missing tangible inn/collision query evidence')
    (out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    lines = ['# High-elf Map0: offline native query evidence', '',
             'Reproduce: `TMPDIR="$PWD/work/tmp" python3 tools/build_high_elf_nav_probe.py`', '',
             f'Native loaded sets: {result["loads"]} (24 regional Maps + 19 existing halo Maps). '
             f'Spatial samples: {len(samples)}.', '',
             f'All {result["unique_loaded_models"]} unique collision models loaded and matched against the '
             f'project manifest; {result["loaded_model_instances"]} populated BIH slots.', '',
             f'Additional cardinal halo Maps absent at runtime: {result["absent_halo_maps"]}. '
             'These are explicitly recorded as absent, not counted as loaded.', '',
             '| Filter | Queries | Complete corridor | Outcomes |', '|---|---:|---:|---|']
    for mode, stats in modes.items():
        lines.append(f'| {mode} | {stats["queries"]} | {stats["complete"]} | {stats["outcomes"]} |')
    inn = result['inn_queries']
    lines += ['', '## Inn exact root6002/nameSet0/group0', '',
              f'{len(inn)} query cases; {sum(r["complete"] == "1" for r in inn)} complete corridors. '
              'Floor and overhead hits are recorded separately in `interiors.tsv`. '
              'No same-floor destination for the lowest covered sample is reported as `NOT_CALLED`; '
              'higher-floor queries are explicitly labelled `upper_floor`.', '',
              '## Tangible collision', '', str(result['rays']), '', '## Manual teleport candidates', '',
              'Native ground+2; walk poly, dry terrain, 9 local ground checks and static VMap headroom. '
              'These are offline geometric candidates, not gameplay guarantees.', '']
    for row in teleports:
        lines.append(f'- Area {row["area"]}: `.go xyz {float(row["x"]):.5f} {float(row["y"]):.5f} '
                     f'{float(row["tele_z"]):.5f} 0` (native ground {row["ground"]}; poly {row["poly"]}).')
    lines += ['', '## Scope', '', *('- ' + limit for limit in result['limits']), '',
              'Raw evidence: `loads.tsv`, `anchors.tsv`, `samples.tsv`, `paths.tsv`, `interiors.tsv`, `rays.tsv`, '
              '`teleports.tsv`; source/runtime hashes and unchanged-input check in `evidence.json`.', '']
    (out / 'REPORT.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, default=CORE)
    parser.add_argument('--runtime', type=Path, default=CORE / 'env/dist/bin')
    parser.add_argument('--source', type=Path, default=ROOT / 'work/elf-map-audit-research/turtle/World/Maps/Azeroth')
    parser.add_argument('--output', type=Path, default=ROOT / 'work/high-elf-native-validation')
    parser.add_argument('--build-only', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / 'work/tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TMPDIR=str(tmp))
    build = args.core / 'build'

    def includes(target):
        flags = (build / target / 'flags.make').read_text()
        return shlex.split(next(line.split('=', 1)[1] for line in flags.splitlines()
                                if line.startswith('CXX_INCLUDES =')))

    link = shlex.split((build / 'src/tools/CMakeFiles/mmaps_generator.dir/link.txt').read_text())
    libs = link[link.index('../common/libcommon.a'):]
    libs = [str((build / 'src/tools' / arg).resolve())
            if arg.endswith('.a') and not Path(arg).is_absolute() else arg for arg in libs]
    # Use the already-built Maps reader and real offline DBC stores, not fake
    # symbols or ignored link errors. No database functions are called.
    terrain = build / 'src/server/game/CMakeFiles/game.dir/Grids/GridTerrainData.cpp.o'
    command = ['clang++', '-std=c++20', '-O2', '-Wall', '-Wextra', '-DENABLE_VMAP_CHECKS',
               *includes('src/common/CMakeFiles/common.dir'),
               *includes('src/server/game/CMakeFiles/game.dir'),
               str(ROOT / 'tools/high_elf_nav_probe.cpp'), str(terrain), '-o', str(out / 'high_elf_nav_probe'),
               '-Wl,--start-group', str(build / 'src/server/shared/libshared.a'),
               str(build / 'src/server/database/libdatabase.a'), *libs, '-Wl,--end-group',
               *shlex.split(subprocess.check_output(['pkg-config', '--libs', 'mysqlclient'], text=True))]
    (out / 'build-command.json').write_text(json.dumps(command, indent=2) + '\n')
    with (out / 'build.log').open('w') as log:
        subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    if args.build_only:
        print(out / 'high_elf_nav_probe')
        return

    terrain_selection = json.loads((ROOT / 'tools/high-elf-terrain-selection.json').read_text())
    selection = terrain_selection['selection']
    mapping = json.loads((ROOT / 'tools/high-elf-map.json').read_text())['area_ids']
    evidence = {'runtime': str(args.runtime.resolve()), 'source_cells': [], 'inputs': {},
                'scope': 'Offline native readers/queries only; no gameplay or movement-generator validation.'}
    cells = []
    # Source MCNK identity selects centers; height is deliberately NOT taken from
    # source or guessed. Native installed Maps/VMaps readers pick the floor.
    for tile, bits in sorted(selection.items()):
        x, y = map(int, tile.split('_'))
        path = args.source / f'Azeroth_{x}_{y}.adt'
        raw = path.read_bytes()
        evidence['inputs'][str(path)] = digest(path)
        if digest(path) != terrain_selection['inputs'][tile][1]:
            raise ValueError(f'Source ADT does not match selected source lock: {path}')
        selected = int.from_bytes(bytes.fromhex(bits), 'little')
        for slot, (offset, *_rest) in enumerate(_adt_layout(raw)[3]):
            if not (selected >> slot) & 1:
                continue
            area = struct.unpack_from('<I', raw, offset + 0x3c)[0]
            if str(area) not in mapping:
                continue
            cx, cy = struct.unpack_from('<II', raw, offset + 12)
            if (cx, cy) != (slot % 16, slot // 16):
                raise ValueError(f'Unexpected MCNK ordering: {path}:{slot}')
            wx = (32 - y - (cy + 0.5) / 16) * (1600 / 3)
            wy = (32 - x - (cx + 0.5) / 16) * (1600 / 3)
            cells.append(f'{x} {y} {cx} {cy} {area} {mapping[str(area)]} {wx:.9f} {wy:.9f}\n')
            evidence['source_cells'].append(dict(tile=tile, slot=slot, source_area=area,
                                                 area=mapping[str(area)], x=wx, y=wy))
    (out / 'cells.txt').write_text(''.join(cells))
    files = {
        'vmaps': sorted(args.runtime.glob('vmaps/000_??_??.vmtile')),
        'mmaps': sorted(args.runtime.glob('mmaps/000????.mmtile')),
    }
    if len(files['vmaps']) != 374 or len(files['mmaps']) != 522:
        raise ValueError(f'Unexpected Map0 inventory: { {k: len(v) for k, v in files.items()} }')
    regional = {tuple(map(int, tile.split('_'))) for tile in selection}
    halo = regional | {(x + dx, y + dy) for x, y in regional for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))}
    maps = []
    evidence['absent_halo_maps'] = []
    for x, y in sorted(halo):
        path = args.runtime / f'maps/000{y:02}{x:02}.map'
        if path.is_file():
            maps.append(path)
        elif (x, y) in regional:
            raise ValueError(f'Missing required regional Map: {path}')
        else:
            evidence['absent_halo_maps'].append(str(path))
    (out / 'maps.txt').write_text(''.join(str(p.resolve()) + '\n' for p in maps))
    for kind, paths in files.items():
        (out / f'{kind}.txt').write_text(''.join(str(p.resolve()) + '\n' for p in paths))
    manifest_path = ROOT / 'data/server/manifest.json'
    manifest = json.loads(manifest_path.read_text())['files']
    expected = {entry['path']: entry for source, entry in manifest.items()
                if source.startswith('high-elf-map/') and entry['kind'] != 'additive-dbc'}
    evidence['manifest_sha256'] = digest(manifest_path)
    evidence['manifest_static_files_verified'] = len(expected)
    for path, entry in expected.items():
        installed = args.runtime / path
        if installed.stat().st_size != entry['size'] or digest(installed) != entry['sha256']:
            raise ValueError(f'Installed static payload differs from manifest: {installed}')
    expected_vmaps = {Path(p).name for p in expected if p.endswith('.vmtile')}
    if expected_vmaps != {p.name for p in files['vmaps']}:
        raise ValueError('Installed VMap tile set differs from complete manifest set')
    # Some shared collision models are owned by older project payloads rather
    # than duplicated under high-elf-map. Include their before/after hashes too.
    all_models = {entry['path']: entry for entry in manifest.values()
                  if entry['path'].startswith('vmaps/') and entry['path'].endswith(('.vmo', '.m2'))}
    paths = [*maps, *files['vmaps'], *files['mmaps'], args.runtime / 'vmaps/000.vmtree',
             args.runtime / 'mmaps/000.mmap', *(args.runtime / f'dbc/{t}.dbc'
                                               for t in ('AreaTable', 'LiquidType', 'WMOAreaTable')),
             *(args.runtime / p for p in expected), *(args.runtime / p for p in all_models)]
    evidence['runtime_sha256_before'] = {str(p): digest(p) for p in paths}
    evidence['probe_sha256'] = digest(out / 'high_elf_nav_probe')
    evidence['terrain_object_sha256'] = digest(terrain)
    with (out / 'run.log').open('w') as log:
        result = subprocess.run([str(out / 'high_elf_nav_probe'), str(args.runtime.resolve()), str(out)],
                                env=env, stdout=log, stderr=subprocess.STDOUT)
    evidence['returncode'] = result.returncode
    evidence['runtime_inputs_unchanged'] = all(digest(Path(p)) == sha
                                              for p, sha in evidence['runtime_sha256_before'].items())
    (out / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(f'Probe exit={result.returncode}; evidence: {out}')
    if result.returncode or not evidence['runtime_inputs_unchanged']:
        raise SystemExit(result.returncode or 1)
    with (out / 'models.tsv').open() as stream:
        native_models = list(csv.DictReader(stream, delimiter='\t'))
    for row in native_models:
        path = 'vmaps/' + row['file']
        if path not in all_models or digest(args.runtime / path) != all_models[path]['sha256']:
            raise ValueError(f'Native loaded model not matching project manifest: {path}')
    evidence['native_loaded_unique_models_manifest_verified'] = len(native_models)
    evidence['native_loaded_model_instances'] = sum(int(row['instances']) for row in native_models)
    (out / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    summarize(out)


if __name__ == '__main__':
    main()
