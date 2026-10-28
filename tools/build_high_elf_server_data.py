#!/usr/bin/env python3
"""Isolated Map0 extraction/navigation build. Never installs or touches SQL.

Run with TMPDIR=$PWD/work/tmp. Subcommands are restartable; input and completed
command hashes are checked before reuse. See OUTPUT/INSTALL.md and report.json.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import threading

from crypt_release_client import extract
from crypt_release_server_data import binary_check, tile_models
from dbc_write import write_dbc_bytes
from high_elf_map_assets import file_hash
from high_elf_map_dbc import apply_delta, parse, require

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'client_patches/archive/source-inputs/high-elf-map'
WDT = r'World\Maps\Azeroth\Azeroth.wdt'


def previous_owned(manifest):
    """Only verified durable project sources confer replacement ownership."""
    if manifest is None:
        return {}
    from apply_project_server_data import inventory, load_json
    inventory(manifest)
    return {r['path']: r for n, r in load_json(manifest.read_bytes())['files'].items()
            if n == 'high-elf-map/' + r['path']}


def owned_collision(name, installed, owned):
    return (re.fullmatch(r'vmaps/He_[0-9a-f]{20}_.+\.wmo\.vmo', name, re.I) is not None
            and name in owned and installed == owned[name]['sha256'])


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')


def subset_wdt(data, tiles):
    out = bytearray(data)
    pos, found = 0, False
    while pos < len(out):
        magic, size = struct.unpack_from('<4sI', out, pos)
        require(pos + 8 + size <= len(out), 'Truncated WDT')
        if magic == b'NIAM':
            require(not found and size == 64 * 64 * 8, 'Invalid MAIN')
            found = True
            for y in range(64):
                for x in range(64):
                    if (x, y) not in tiles:
                        struct.pack_into('<II', out, pos + 8 + (y * 64 + x) * 8, 0, 0)
        pos += 8 + size
    require(found and pos == len(out), 'Missing MAIN')
    return bytes(out)


def map_name(x, y):
    return f'000{y:02}{x:02}.map'


def mmap_name(x, y):
    return f'000{y:02}{x:02}.mmtile'


def cardinal_halo(tiles):
    tiles = set(tiles)
    return {(nx, ny) for x, y in tiles for nx, ny in
            ((x-1, y), (x+1, y), (x, y-1), (x, y+1))
            if 0 <= nx < 64 and 0 <= ny < 64} - tiles


def official(path):
    """Explicit Blizzard-name allowlist, excluding snapshot custom archives."""
    name = path.name
    if path.parent.name == 'Data':
        return bool(re.fullmatch(r'(common(?:-2)?|expansion|lichking|patch(?:-[23])?)\.MPQ', name, re.I))
    locale = path.parent.name
    return bool(re.fullmatch(r'(?:locale|speech|expansion-(?:locale|speech)|lichking-(?:locale|speech)|patch)-'
                             + locale + r'(?:-[23])?\.MPQ', name, re.I))


class Build:
    def __init__(self, args):
        self.a, self.out = args, args.output.resolve()
        require(self.out.is_relative_to(ROOT / 'work'), 'Output must be below setup/work')
        require(self.out not in (ROOT / 'work', ROOT / 'work/tmp'), 'Use a dedicated output')
        self.out.mkdir(exist_ok=True)
        (self.out / 'logs').mkdir(exist_ok=True)
        self.mpq = ROOT / 'tools/mpq'
        self.bin = args.server
        self.lockfile = self.out / 'inputs.json'
        self.lock = json.loads(self.lockfile.read_text()) if self.lockfile.exists() else {}
        self.wrapper_sha256 = file_hash(Path(__file__))
        self.audit_lock = threading.Lock()

    def run(self, label, command, cwd=None, allowed=(0,)):
        command = list(map(str, command))
        record = self.out / 'logs' / (label + '.json')
        if record.exists():
            old = json.loads(record.read_text())
            require(old['command'] == command and old['returncode'] in allowed,
                    'Previous failed/different command: ' + label)
            if old.get('wrapper_sha256') != self.wrapper_sha256:
                require(self.a.reuse_previous_wrapper,
                        'Cached output uses another wrapper revision: ' + label +
                        '; inspect it before using --reuse-previous-wrapper')
                with self.audit_lock:
                    auditfile = self.out / 'reuse-audit.json'
                    audit = json.loads(auditfile.read_text()) if auditfile.exists() else {}
                    audit[label] = dict(original_record_sha256=file_hash(record),
                                        previous_wrapper=old.get('wrapper_sha256'),
                                        accepted_by_wrapper=self.wrapper_sha256)
                    dump(auditfile, audit)
            return
        with (self.out / 'logs' / (label + '.log')).open('wb') as log:
            p = subprocess.run(command, cwd=cwd or self.out, stdout=log,
                               stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        dump(record, dict(command=command, cwd=str(cwd or self.out), returncode=p.returncode,
                          wrapper_sha256=self.wrapper_sha256))
        require(p.returncode in allowed, 'Command failed: ' + label)

    def pin(self, path):
        path = path.resolve()
        info = dict(size=path.stat().st_size, sha256=file_hash(path))
        require(str(path) not in self.lock or self.lock[str(path)] == info, 'Input changed: ' + str(path))
        self.lock[str(path)] = info
        return info

    def validate(self):
        for path, expected in self.lock.items():
            require(Path(path).stat().st_size == expected['size'] and file_hash(Path(path)) == expected['sha256'],
                    'Pinned input changed: ' + path)

    def add(self, archive, path, member):
        self.run('add-' + archive.parent.parent.name + '-' + path.stem,
                 [self.mpq, 'add', archive, path, member])
        require(extract(self.mpq, archive, member) == path.read_bytes(), 'MPQ add readback mismatch')

    def prepare(self):
        if (self.out / 'prepared.json').exists():
            self.validate()
            return
        require(not self.lock, 'Incomplete prepare; inspect and use a fresh staging')
        for p in [self.mpq, self.a.terrain / 'manifest.json',
                  self.a.assets / 'manifest.json', SOURCE / 'source-lock.json']:
            self.pin(p)
        if self.a.previous_manifest is not None:
            previous_owned(self.a.previous_manifest)
            self.pin(self.a.previous_manifest)
        for name in ('map_extractor', 'vmap4_extractor', 'vmap4_assembler', 'mmaps_generator', 'mmaps-config.yaml'):
            self.pin(self.bin / name)
        terrain = json.loads((self.a.terrain / 'manifest.json').read_text())
        assets = json.loads((self.a.assets / 'manifest.json').read_text())
        tiles = {tuple(t['tile']) for t in terrain['tiles']}
        require(len(tiles) == 24 and assets['asset_closure_complete'], 'Invalid final input closure')
        self.tiles = sorted(tiles)
        dbc = self.out / 'server-dbc'
        dbc.mkdir()
        for name in ('Map', 'AreaTable', 'WMOAreaTable', 'LiquidType', 'WorldMapArea', 'WorldMapOverlay'):
            baseline = self.bin / 'dbc' / (name + '.dbc')
            self.pin(baseline)
            raw = baseline.read_bytes()
            if name in ('AreaTable', 'WMOAreaTable', 'WorldMapArea', 'WorldMapOverlay'):
                donor = SOURCE / 'deltas' / (name + '.dbc')
                self.pin(donor)
                if name == 'WorldMapOverlay':
                    from high_elf_map_cartography import merge_overlays
                    raw = merge_overlays(raw, donor.read_bytes())
                else:
                    raw = apply_delta(name, raw, donor.read_bytes())
            (dbc / (name + '.dbc')).write_bytes(raw)
        rows, strings = parse((dbc / 'Map.dbc').read_bytes(), 66)
        require(any(r[0] == 800 for r in rows), 'Full server Map must retain crypt800')
        onlymap = self.out / 'Map.only0.dbc'
        onlymap.write_bytes(write_dbc_bytes(66, [r for r in rows if r[0] == 0], strings))
        official_inputs = sorted(p for p in (self.a.stock / 'Data').rglob('*')
                                 if p.is_file() and official(p))
        require(len(official_inputs) >= 10, 'Missing official stock archives')
        regular = sorted(p for p in (self.a.client / 'Data').rglob('*') if p.suffix.lower() == '.mpq')
        for p in official_inputs + regular:
            self.pin(p)
        for variant in ('client-full', 'client-maps', 'client-native'):
            data = self.out / variant / 'Data'
            data.mkdir(parents=True)
            for p in official_inputs:
                target = data / p.relative_to(self.a.stock / 'Data')
                target.parent.mkdir(exist_ok=True)
                target.symlink_to(p)
                # Linux native tools construct locale paths with canonical case.
                if p.parent.name in ('enUS', 'esES'):
                    canonical = re.sub(p.parent.name, p.parent.name, p.name, flags=re.I)
                    canonical = re.sub(r'\.mpq$', '.MPQ', canonical, flags=re.I)
                    alias = target.with_name(canonical)
                    if alias != target and not alias.exists():
                        alias.symlink_to(p)
            if variant != 'client-native':
                for p in regular:
                    target = data / p.relative_to(self.a.client / 'Data')
                    target.parent.mkdir(exist_ok=True)
                    require(not target.exists(), 'Regular archive conflicts with official archive')
                    shutil.copy2(p, target)
            else:
                self.run('create-native-T', [self.mpq, 'create', data / 'patch-T.MPQ'])
            arc = data / 'patch-T.MPQ'
            if variant != 'client-native':
                for tile in assets['tiles']:
                    require(hashlib.sha256(extract(self.mpq, arc, tile['target'])).hexdigest() == tile['sha256'],
                            'Regular T differs from final assets/terrain: ' + tile['target'])
            for name in ('AreaTable', 'WMOAreaTable', 'LiquidType'):
                self.add(arc, dbc / (name + '.dbc'), 'DBFilesClient\\' + name + '.dbc')
            self.add(arc, onlymap, r'DBFilesClient\Map.dbc')
        full_t = self.out / 'client-full/Data/patch-T.MPQ'
        full_wdt = extract(self.mpq, full_t, WDT, optional=True)
        if full_wdt is None:
            for name in ('patch-3.MPQ', 'patch-2.MPQ', 'patch.MPQ', 'lichking.MPQ',
                         'expansion.MPQ', 'common-2.MPQ', 'common.MPQ'):
                p = self.a.stock / 'Data' / name
                if p.is_file():
                    full_wdt = extract(self.mpq, p, WDT, optional=True)
                    if full_wdt is not None:
                        break
        require(full_wdt is not None, 'Missing continent WDT')
        (self.out / 'Azeroth.full.wdt').write_bytes(full_wdt)
        limited = self.out / 'Azeroth.subset.wdt'
        limited.write_bytes(subset_wdt(full_wdt, tiles))
        for variant in ('client-maps', 'client-native'):
            self.add(self.out / variant / 'Data/patch-T.MPQ', limited, WDT)
        self.add(full_t, self.out / 'Azeroth.full.wdt', WDT)
        for variant in ('client-full', 'client-maps', 'client-native'):
            self.pin(self.out / variant / 'Data/patch-T.MPQ')
        dump(self.lockfile, self.lock)
        dump(self.out / 'prepared.json', dict(tiles=self.tiles, full_wdt_sha256=file_hash(self.out / 'Azeroth.full.wdt'),
             selected_cells={','.join(map(str, t['tile'])): t['selected_source_cells'] for t in terrain['tiles']},
             note='Map.only0 and subset WDT are extractor-only; never deploy them'))

    def geometry(self):
        self.validate()
        for variant, dest in (('client-maps', 'geometry'), ('client-native', 'native')):
            target = self.out / dest
            target.mkdir(exist_ok=True)
            self.run('maps-' + dest, [self.bin / 'map_extractor', '-i', self.out / variant,
                                     '-o', target, '-e', '1'], cwd=target)
            require(len(list((target / 'maps').glob('*.map'))) == 24, 'Expected exactly 24 maps')
        geometry = self.out / 'geometry'
        self.run('vmap-extractor', [self.bin / 'vmap4_extractor', '-d',
                 str(self.out / 'client-full/Data') + '/', '--only', '0'], cwd=geometry)
        (geometry / 'vmaps').mkdir(exist_ok=True)
        self.run('vmap-assembler', [self.bin / 'vmap4_assembler', geometry / 'Buildings',
                                  geometry / 'vmaps'], cwd=geometry)

    def locales(self):
        """Canonicalize case-sensitive stock locale links and verify geometry.

        Also repairs staging from the first wrapper revision, whose allowlist
        missed lowercase Spanish official archives. No regular copy is changed.
        """
        self.validate()
        for p in sorted((self.a.stock / 'Data').rglob('*')):
            if not p.is_file() or not official(p):
                continue
            self.pin(p)
            for variant in ('client-full', 'client-maps', 'client-native'):
                target = self.out / variant / 'Data' / p.relative_to(self.a.stock / 'Data')
                target.parent.mkdir(exist_ok=True)
                if not target.exists():
                    target.symlink_to(p)
                if p.parent.name in ('enUS', 'esES'):
                    canonical = re.sub(p.parent.name, p.parent.name, p.name, flags=re.I)
                    canonical = re.sub(r'\.mpq$', '.MPQ', canonical, flags=re.I)
                    alias = target.with_name(canonical)
                    if not alias.exists():
                        alias.symlink_to(p)
        dump(self.lockfile, self.lock)
        check = self.out / 'locale-verification'
        check.mkdir(exist_ok=True)
        (check / 'vmaps').mkdir(exist_ok=True)
        self.run('vmap-locales-extractor', [self.bin / 'vmap4_extractor', '-d',
                 str(self.out / 'client-full/Data') + '/', '--only', '0'], cwd=check)
        self.run('vmap-locales-assembler', [self.bin / 'vmap4_assembler', check / 'Buildings',
                                          check / 'vmaps'], cwd=check)
        old = self.out / 'geometry/vmaps'
        for p in sorted(old.glob('000*')):
            require(file_hash(p) == file_hash(check / 'vmaps' / p.name), 'Locale changed map0 geometry')
            if p.suffix == '.vmtile':
                for name in tile_models(p.read_bytes()):
                    require(file_hash(old / name) == file_hash(check / 'vmaps' / name),
                            'Locale changed collision model: ' + name)
        require({p.name for p in old.glob('000*')} ==
                {p.name for p in (check / 'vmaps').glob('000*')}, 'Locale changed tile coverage')
        dump(check / 'verified.json', dict(map0_tiles_and_tree_identical=True,
             referenced_collision_models_identical=True))

    def navigation(self):
        self.validate()
        tiles = [tuple(t) for t in json.loads((self.out / 'prepared.json').read_text())['tiles']]
        geometry = self.out / 'geometry'
        nav = self.out / 'navigation'
        nav.mkdir(exist_ok=True)
        for directory in ('maps', 'mmaps'):
            (nav / directory).mkdir(exist_ok=True)
        if not (nav / 'vmaps').exists():
            (nav / 'vmaps').symlink_to(geometry / 'vmaps', target_is_directory=True)
        # Generator reads cardinal neighbor height strips; keep all installed
        # native maps visible but replace only our 24 generated inputs.
        for p in sorted((self.bin / 'maps').glob('000*.map')):
            target = nav / 'maps' / p.name
            if not target.exists():
                target.symlink_to(p)
        for p in sorted((geometry / 'maps').glob('*.map')):
            target = nav / 'maps' / p.name
            if target.is_symlink():
                target.unlink()
            if not target.exists():
                target.symlink_to(p)
        primary = set(tiles)
        halo = sorted(t for t in cardinal_halo(primary)
                      if (nav / 'maps' / map_name(*t)).exists() or
                      (nav / 'vmaps' / f'000_{t[0]:02}_{t[1]:02}.vmtile').exists())
        tiles += halo
        config = nav / 'mmaps-config.yaml'
        config.write_text((self.bin / 'mmaps-config.yaml').read_text().replace('dataDir: "./"',
                                                                          'dataDir: ' + json.dumps(str(nav))))
        dependencies = {}
        for x, y in tiles:
            for nx, ny in ((x, y), (x-1, y), (x+1, y), (x, y-1), (x, y+1)):
                p = nav / 'maps' / map_name(nx, ny)
                if p.exists():
                    dependencies[str(p)] = dict(realpath=str(p.resolve()), sha256=file_hash(p))
                    self.pin(p)
        dump(self.lockfile, self.lock)
        dump(nav / 'dependencies.json', dependencies)
        # Single-tile builds all write 000.mmap. Generate first synchronously,
        # then workers use identical parameters; no live output path is used.
        def generate(tile):
            x, y = tile
            self.run(f'mmap-{x:02}-{y:02}', [self.bin / 'mmaps_generator', '0', '--config', config,
                     '--threads', '1', '--tile', f'{x},{y}', '--silent'], cwd=nav)
            target = nav / 'mmaps' / mmap_name(x, y)
            if not target.is_file():
                selected = json.loads((self.out / 'prepared.json').read_text())['selected_cells']
                require(selected.get(f'{x},{y}', 0) == 0 and
                        not (self.bin / 'mmaps' / target.name).exists(),
                        'Generator produced no tile for changed/native-navigable terrain: ' + str(tile))
            else:
                binary_check(target.name, target.read_bytes())
        generate(tiles[0])
        with ThreadPoolExecutor(max_workers=self.a.jobs) as pool:
            list(pool.map(generate, tiles[1:]))
        dump(nav / 'completed.json', dict(primary=sorted(primary), halo=halo,
             generated=[list(t) for t in tiles if (nav / 'mmaps' / mmap_name(*t)).exists()],
             empty=[list(t) for t in tiles if not (nav / 'mmaps' / mmap_name(*t)).exists()]))
        self.validate()

    def report(self):
        self.validate()
        owned = previous_owned(self.a.previous_manifest)
        prepared = json.loads((self.out / 'prepared.json').read_text())
        geometry, nav = self.out / 'geometry', self.out / 'navigation'
        require((nav / 'completed.json').is_file(), 'Navigation incomplete')
        completion = json.loads((nav / 'completed.json').read_text())
        require(len(completion['primary']) == 24 and all(
            (nav / 'mmaps' / mmap_name(*t)).is_file() for t in completion['generated']),
            'Incomplete navigation output')
        files, closure, comparisons = {}, set(), {}
        for directory, base, pattern in [('maps', geometry, '*.map'), ('vmaps', geometry, '000*'),
                                          ('mmaps', nav, '000*'), ('dbc', self.out, '*.dbc')]:
            folder = self.out / 'server-dbc' if directory == 'dbc' else base / directory
            for p in sorted(folder.glob(pattern)):
                if p.suffix == '.vmtile':
                    closure.update(tile_models(p.read_bytes()))
                if directory != 'dbc':
                    binary_check(p.name, p.read_bytes())
                relative = directory + '/' + p.name
                live = self.bin / relative
                info = dict(source=str(p.relative_to(self.out)), size=p.stat().st_size, sha256=file_hash(p))
                info['installed_sha256'] = file_hash(live) if live.is_file() else None
                info['action'] = ('identical' if info['installed_sha256'] == info['sha256'] else
                                  'replace-scoped' if live.exists() else 'add')
                if directory == 'maps':
                    native = self.out / 'native/maps' / p.name
                    info['native_extraction_sha256'] = file_hash(native)
                    if info['sha256'] == info['native_extraction_sha256']:
                        info['action'] = 'omit-native-unchanged'
                files[relative] = info
        missing, conflicts = [], []
        for name in sorted(closure):
            p = geometry / 'vmaps' / name
            if not p.is_file():
                missing.append(name)
                continue
            h = file_hash(p)
            require(p.read_bytes()[:8] == b'VMAP_4.8', 'Invalid collision model header: ' + name)
            live = self.bin / 'vmaps' / name
            installed = file_hash(live) if live.is_file() else None
            action = 'identical' if h == installed else 'add' if installed is None else 'CONFLICT'
            if action == 'CONFLICT' and owned_collision('vmaps/' + name, installed, owned):
                action = 'replace-scoped'
            if action == 'CONFLICT':
                conflicts.append(name)
            files['vmaps/' + name] = dict(source=str(p.relative_to(self.out)), size=p.stat().st_size,
                                         sha256=h, installed_sha256=installed, action=action)
        for tile in prepared['tiles']:
            x, y = tile
            native = self.out / 'native/maps' / map_name(x, y)
            live = self.bin / 'maps' / native.name
            comparisons[native.name] = dict(native_sha256=file_hash(native),
                 installed_sha256=file_hash(live) if live.exists() else None)
        logs = {}
        for p in sorted((self.out / 'logs').glob('*.json')):
            log = p.with_suffix('.log')
            lines = log.read_text(errors='replace').splitlines()
            diagnostics = [line for line in lines if re.search(r'error|failed|couldn.t|can.t|invalid|not found', line, re.I)]
            logs[p.stem] = dict(**json.loads(p.read_text()), sha256=file_hash(log), diagnostics=diagnostics)
        counts = {suffix: sum(Path(n).suffix == suffix for n in files)
                  for suffix in ('.map', '.vmtree', '.vmtile', '.vmo', '.m2', '.mmap', '.mmtile', '.dbc')}
        generated_params = struct.unpack('<5f2I', (nav / 'mmaps/000.mmap').read_bytes())
        installed_params = struct.unpack('<5f2I', (self.bin / 'mmaps/000.mmap').read_bytes())
        require(generated_params[:5] == installed_params[:5] and
                generated_params[6] == installed_params[6], 'MMap parameter geometry/capacity mismatch')
        # All surviving native tiles must keep unique Detour coordinates and fit
        # the replacement map's allocation. References are runtime-generated;
        # these payloads carry coordinates, not old VMap tree node indices.
        surviving = {p.name: p for p in (self.bin / 'mmaps').glob('000*.mmtile')}
        surviving.update({p.name: p for p in (nav / 'mmaps').glob('000*.mmtile')})
        coords, surviving_info = set(), {}
        for name, p in sorted(surviving.items()):
            data = p.read_bytes()
            binary_check(name, data)
            header = struct.unpack_from('<15I', data, 56)
            coordinate = tuple(header[2:5])
            require(coordinate not in coords and 0 < header[6] <= generated_params[6],
                    'Duplicate coordinate/invalid poly count: ' + name)
            coords.add(coordinate)
            surviving_info[name] = dict(source=str(p), sha256=file_hash(p),
                detour_coordinate=coordinate, polygons=header[6], vertices=header[7])
        require(len(surviving) <= generated_params[5], 'Insufficient map0 MMap tile capacity')
        generated_vtiles = {p.name for p in (geometry / 'vmaps').glob('000*.vmtile')}
        installed_vtiles = {p.name for p in (self.bin / 'vmaps').glob('000*.vmtile')}
        report = dict(schema=1, status='staging-only', counts=counts, missing_models=missing,
                       collision_model_count=len(closure),
                       previous_manifest_sha256=file_hash(self.a.previous_manifest)
                           if self.a.previous_manifest else None,
                      wrapper_sha256=file_hash(Path(__file__)),
                      navigation=completion,
                      mmap_consistency=dict(generated_params=generated_params, installed_params=installed_params,
                                            final_tile_count=len(surviving), tiles=surviving_info),
                      vmap_coverage=dict(generated=len(generated_vtiles), installed=len(installed_vtiles),
                          new_tiles=sorted(generated_vtiles-installed_vtiles),
                          stale_installed_tiles=sorted(installed_vtiles-generated_vtiles)),
                      locale_verification=json.loads((self.out / 'locale-verification/verified.json').read_text())
                          if (self.out / 'locale-verification/verified.json').exists() else None,
                      collision_conflicts=conflicts, files=files, logs=logs,
                      native_maps_vs_installed=comparisons, tiles=prepared['tiles'],
                      coordinate_convention='ADT X,Y -> --tile X,Y; map/mmtile 000YYXX; vmtile 000_XX_YY',
                      deployment_performed=False, runtime_gameplay_test='NOT RUN')
        dump(self.out / 'report.json', report)
        dump(self.out / 'intended-files.json', {n: v for n, v in files.items()
             if v['action'] in ('replace-scoped', 'add')})
        (self.out / 'INSTALL.md').write_text((ROOT / 'docs/turtle-wow/high-elf-server-data.md').read_text())
        print(json.dumps(dict(counts=counts, missing_models=len(missing), collision_conflicts=len(conflicts))))
        require(not missing and not conflicts, 'Collision closure failed; see report.json')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('phase', choices=('prepare', 'geometry', 'locales', 'navigation', 'report', 'all'))
    ap.add_argument('--output', type=Path, default=ROOT / 'work/high-elf-server-build')
    ap.add_argument('--stock', type=Path, default=Path('/home/dev/wow-335'))
    ap.add_argument('--client', type=Path, default=ROOT / 'client_patches/regular_client')
    ap.add_argument('--terrain', type=Path, default=ROOT / 'work/high-elf-terrain-final')
    ap.add_argument('--assets', type=Path, default=ROOT / 'work/high-elf-assets-final-v2')
    ap.add_argument('--server', type=Path, default=Path('/home/dev/azerothcore/env/dist/bin'))
    ap.add_argument('--jobs', type=int, default=2)
    ap.add_argument('--previous-manifest', type=Path,
                    help='Verified durable manifest authorizing exact previous custom WMO hashes')
    ap.add_argument('--reuse-previous-wrapper', action='store_true',
                    help='Explicitly accept inspected cached commands from older wrapper revisions; audited')
    args = ap.parse_args()
    require(1 <= args.jobs <= 4, 'Use 1-4 workers')
    os.environ['TMPDIR'] = str(ROOT / 'work/tmp')
    import tempfile
    tempfile.tempdir = os.environ['TMPDIR']
    b = Build(args)
    for phase in ('prepare', 'geometry', 'locales', 'navigation', 'report'):
        if args.phase in (phase, 'all'):
            getattr(b, phase)()


if __name__ == '__main__':
    main()
