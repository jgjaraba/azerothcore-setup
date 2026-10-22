#!/usr/bin/env python3
"""Build the isolated r3 cartography package from read-only snapshots and r2.

No research-directory inputs or third-party Python packages are required. MPQ
access uses tools/mpq (StormLib). Output must be new; nothing is installed.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import struct
import subprocess

from dbc_write import read_dbc_bytes, write_dbc_bytes

ROOT = Path(__file__).resolve().parent.parent
TRS = r'Textures\Minimap\md5translate.trs'
WMA = r'DBFilesClient\WorldMapArea.dbc'
NATIVE = r'WMO\Dungeon\MD_Crypt\MD_Crypt_D'
TARGET = r'WMO\Custom\Turtle800\tw800crypt'
TARGET_WMO = r'World\wmo\Custom\Turtle800\tw800crypt'
SOURCE_WMO = r'World\wmo\Dungeon\MD_Crypt\MD_Crypt_D'
R2_HASHES = {
    'Data/patch-T.MPQ': '6785296c4b54feb4ca2dc2bc918b6a9580812af118cd1f896edbb90d3cb13521',
    'Data/patch-Z.mpq': 'cad32e8e64b89c862b857171fa413557c78e11f04aa2274c2d1af19571a3a022',
    'Data/esES/patch-esES-Z.MPQ': '25708c1a31b5532f111222007861e7bd50aad2beff24b40a27d5331c48958b50',
}
WMA_HASH = '178b3832815d2881a543fbf440901226dad95b1fac1d85a065df7a813cc4571b'
TRS_HASH = '9d372059022d1d8c267f1f9aa97aca02cbbf4d3142a5a2eeaca0393d0f8c8226'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def normalize(name):
    return name.replace('/', '\\').lower()


def safe_relative(name):
    require(not any(ord(c) < 32 or c == '|' for c in name), 'Unsafe archive name')
    parts = name.replace('\\', '/').split('/')
    require(all(p and p not in ('.', '..') and ':' not in p for p in parts),
            f'Unsafe archive path: {name}')
    return Path(*parts)


def parse_trs(data):
    """Return normalized logical keys; reject even equal duplicate entries."""
    result = {}
    for number, line in enumerate(data.decode('ascii').splitlines(), 1):
        if not line.strip() or line.lower().startswith('dir: '):
            continue
        # Logical WMO paths legitimately contain spaces; the delimiter is TAB.
        fields = line.split('\t')
        require(len(fields) == 2, f'Invalid TRS line {number}')
        key, value = fields
        safe_relative(key)
        safe_relative(value)
        require(value.lower().endswith('.blp'), f'Invalid TRS resource: {value}')
        require(key.lower().endswith('.blp'), 'Invalid TRS key')
        canonical = normalize(key)
        require(canonical not in result, f'Duplicate TRS key: {key}')
        result[canonical] = (key, value)
    return result


def merge_trs(baseline, additions):
    existing = parse_trs(baseline)
    seen, lines, directory = set(existing), [], None
    newline = '\r\n' if b'\r\n' in baseline else '\n'
    for key, value in additions:
        canonical = normalize(key)
        require(canonical not in seen, f'TRS collision: {key}')
        seen.add(canonical)
        parent = key.rsplit('\\', 1)[0]
        if parent != directory:
            lines.append('dir: ' + parent)
            directory = parent
        lines.append(f'{key}\t{value}')
    if not lines:
        return baseline
    separator = b'' if baseline.endswith(b'\n') else newline.encode()
    merged = baseline + separator + (newline.join(lines) + newline).encode('ascii')
    parsed = parse_trs(merged)
    require(len(parsed) == len(existing) + len(additions), 'TRS count mismatch')
    require(all(parsed[k] == v for k, v in existing.items()), 'Baseline TRS changed')
    return merged


def blp_dimensions(data):
    """Validate the BLP2/DXT1 family used here, including all mip ranges."""
    require(len(data) >= 148 and data[:4] == b'BLP2', 'Invalid BLP2 header')
    kind, encoding, alpha, alpha_encoding, mips, width, height = struct.unpack_from(
        '<I4B2I', data, 4)
    require(kind == 1 and encoding == 2 and alpha in (0, 1) and
            alpha_encoding == 0 and mips in (0, 1), 'Unsupported BLP2 encoding')
    require(all(1 <= d <= 4096 and d & (d - 1) == 0 for d in (width, height)),
            'Invalid BLP dimensions')
    offsets = struct.unpack_from('<16I', data, 20)
    sizes = struct.unpack_from('<16I', data, 84)
    require(offsets[0] and sizes[0], 'Missing BLP first mip')
    ranges = []
    ended = False
    for level, (offset, size) in enumerate(zip(offsets, sizes)):
        if not offset and not size:
            ended = True
            continue
        require(not ended and offset >= 148 and size > 0 and offset + size <= len(data),
                'Invalid BLP mip range')
        require(mips or level == 0, 'Unexpected BLP mip')
        w, h = max(1, width >> level), max(1, height >> level)
        require(size == ((w + 3) // 4) * ((h + 3) // 4) * 8, 'Invalid DXT1 mip size')
        require(all(offset + size <= a or offset >= b for a, b in ranges),
                'Overlapping BLP mips')
        ranges.append((offset, offset + size))
    return [width, height]


def dbc(data, fields):
    require(len(data) >= 20 and data[:4] == b'WDBC', 'Invalid WDBC header')
    count, actual, size, strings = struct.unpack_from('<4I', data, 4)
    require(actual == fields and size == fields * 4 and
            len(data) == 20 + count * size + strings, 'Invalid WDBC layout')
    return read_dbc_bytes(data)


def append_worldmap_area(baseline, turtle):
    _, rows, strings = dbc(baseline, 11)
    _, source_rows, source_strings = dbc(turtle, 8)
    candidates = [r for r in source_rows if r[0] == 674]
    require(len(candidates) == 1, 'Missing/duplicate Turtle WorldMapArea 674')
    source = candidates[0]
    require(source[1:3] == [800, 5086], 'Unexpected Turtle WorldMapArea identity')
    offset = source[3]
    require(offset < len(source_strings), 'Invalid source name offset')
    end = source_strings.find(b'\0', offset)
    require(end >= 0, 'Unterminated source name')
    name = source_strings[offset:end]
    require(name == b'KarazhanCrypt', 'Unexpected source worldmap name')
    bounds = struct.unpack('<4f', struct.pack('<4I', *source[4:8]))
    require(all(math.isfinite(v) for v in bounds) and bounds[0] != bounds[1] and
            bounds[2] != bounds[3], 'Invalid source worldmap bounds')
    for row in rows:
        require(row[0] != 674 and row[1] != 800 and row[2] != 5086,
                'WorldMapArea ID/map/area collision')
    new = [674, 800, 5086, len(strings), *source[4:8], 0xffffffff, 0, 0]
    merged = write_dbc_bytes(11, rows + [new], strings + name + b'\0')
    _, actual_rows, actual_strings = dbc(merged, 11)
    require(actual_rows[:-1] == rows and actual_strings[:len(strings)] == strings,
            'WorldMapArea baseline changed')
    require(merged[20:20 + len(rows)*44] == baseline[20:20 + len(rows)*44],
            'WorldMapArea record bytes changed')
    return merged, dict(rows_before=len(rows), rows_after=len(actual_rows),
                        rows_preserved_byteexact=True, strings_preserved_byteexact=True,
                        original_strings_sha256=sha(strings), row=new, bounds=bounds)


def chunks(data):
    result, offset = {}, 0
    while offset < len(data):
        require(offset + 8 <= len(data), 'Truncated WMO chunk header')
        magic = data[offset:offset+4][::-1].decode('ascii')
        size = struct.unpack_from('<I', data, offset + 4)[0]
        require(offset + 8 + size <= len(data) and magic not in result,
                'Invalid/duplicate WMO chunk')
        result[magic] = data[offset+8:offset+8+size]
        offset += 8 + size
    return result


def group_header(data):
    header = chunks(data)['MOGP']
    require(len(header) >= 68, 'Short MOGP header')
    bbox = list(struct.unpack_from('<6f', header, 12))
    require(all(math.isfinite(v) for v in bbox), 'Invalid MOGP bounds')
    return dict(groupid=struct.unpack_from('<I', header, 56)[0], bbox=bbox)


def hybrid_reasons(target, source, native_images, turtle_images):
    # Exterior groups have no interior minimap in either family: terrain applies.
    if not native_images and not turtle_images:
        return []
    reasons = []
    if any(abs(target['bbox'][i] - source['bbox'][i]) > 1e-4 for i in (0, 1, 3, 4)):
        reasons.append('MOGP XY bbox differs (tolerance 1e-4)')
    if len(native_images) != len(turtle_images):
        reasons.append('image count differs')
    if set(native_images) != set(turtle_images):
        reasons.append('image grid differs')
    if any(native_images[k]['dimensions'] != turtle_images[k]['dimensions']
           for k in native_images.keys() & turtle_images.keys()):
        reasons.append('BLP dimensions differ')
    return reasons


def match_groups(targets, sources):
    """Join by stable MOGP identity; array indices are only output names."""
    by_id = {g['groupid']: g for g in sources}
    require(len(by_id) == len(sources) and
            len({g['groupid'] for g in targets}) == len(targets), 'Duplicate MOGP group ID')
    require(set(by_id) == {g['groupid'] for g in targets}, 'WMO group ID sets differ')
    return [(target, by_id[target['groupid']]) for target in targets]


class Builder:
    def __init__(self, output, w335, turtle, base):
        self.out, self.w335, self.turtle, self.base = output, w335, turtle, base
        require(not output.exists(), 'Use a fresh output directory')
        for source in (w335, turtle, base):
            require(source.is_dir(), f'Missing source: {source}')
            require(not output.is_relative_to(source) and not source.is_relative_to(output),
                    'Output and inputs must not overlap')
        require(output.is_relative_to(ROOT / 'work'), 'Output must be under setup/work')
        output.mkdir(parents=True)
        self.mpq = ROOT / 'tools/mpq'
        self.sources, self.archives, self.cache, self.payload = [], {}, {}, {}
        self.audit = []

    def run(self, *args):
        return subprocess.run([str(self.mpq), *map(str, args)], capture_output=True, check=True).stdout

    def archive(self, path):
        if str(path) not in self.archives:
            self.archives[str(path)] = dict(sha256=file_sha(path), size=path.stat().st_size)

    def extract(self, archive, name, optional=False):
        cache_key = (str(archive), normalize(name))
        if cache_key in self.cache:
            data = self.cache[cache_key]
            require(optional or data is not None, f'Missing {name} in {archive}')
            return data
        require(archive.is_file(), f'Missing archive: {archive}')
        self.archive(archive)
        # Stable provenance directory, independent of output path.
        label = sha(str(archive).encode())[:12] + '-' + archive.name
        dest = self.out / 'source' / label / safe_relative(name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run([str(self.mpq), 'extract-one', str(archive), name, str(dest)],
                              capture_output=True)
        if proc.returncode:
            require(optional and proc.stderr.strip() == b'ERROR: file not found in archive',
                    f'Extraction failed: {archive}: {name}: {proc.stderr.decode()}')
            self.cache[cache_key] = None
            return None
        data = dest.read_bytes()
        self.sources.append(dict(archive=str(archive), member=name,
                                 extracted=str(dest.relative_to(self.out)), size=len(data), sha256=sha(data)))
        self.cache[cache_key] = data
        return data

    def put(self, name, data):
        key = normalize(name)
        require(key not in self.payload, f'Payload collision: {name}')
        dest = self.out / 'payload' / safe_relative(name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        self.payload[key] = (name, dest)

    def audit_tables(self, snapshots):
        for archive in snapshots + [self.base / p for p in R2_HASHES]:
            hits = {}
            for name in (WMA, TRS):
                data = self.extract(archive, name, optional=True)
                hits[name] = None if data is None else sha(data)
                if archive.is_relative_to(self.base):
                    require(data is None, f'Unexpected r2 cartography override: {archive}')
                elif data is not None:
                    # Detect unresearched later numbered/custom/locale overrides.
                    stem = archive.stem.lower()
                    if name == TRS:
                        require(stem in ('common', 'common-2', 'expansion', 'lichking',
                                         'patch', 'patch-2', 'patch-3'),
                                f'Unexpected TRS override: {archive}')
                    elif 'patch' in stem:
                        suffix = stem.rsplit('-', 1)[-1]
                        require(suffix in ('patch', 'enus', 'eses', '2', '3', 'm', 'n'),
                                f'Unexpected WorldMapArea override: {archive}')
                        if suffix == 'n':
                            require(sha(data) == WMA_HASH, 'Locale N WorldMapArea mismatch')
            self.audit.append(dict(archive=str(archive), members=hits))

    def turtle_image(self, value, archives):
        require(re.fullmatch(r'[0-9a-f]{32}\.blp', value, re.I), 'Expected Turtle MD5 basename')
        for archive in archives:
            data = self.extract(archive, 'Textures\\Minimap\\' + value, optional=True)
            if data is not None:
                return dict(value=value, dimensions=blp_dimensions(data), sha256=sha(data),
                            archive=str(archive)), data
        raise ValueError(f'Turtle texture unresolved: {value}')

    def import_image(self, value, data, snapshots):
        # Namespace every imported minimap (including terrain), so native hashes
        # cannot be silently clobbered. Probe by name, not listfile completeness.
        renamed = 'tw800_' + value
        name = 'Textures\\Minimap\\' + renamed
        for archive in snapshots + [self.base / p for p in R2_HASHES]:
            old = self.extract(archive, name, optional=True)
            require(old is None or old == data, f'Imported texture collision: {archive}: {name}')
        if normalize(name) not in self.payload:
            self.put(name, data)
        else:
            require(self.payload[normalize(name)][1].read_bytes() == data, 'Import conflict')
        return renamed

    def build(self):
        for relative, expected in R2_HASHES.items():
            path = self.base / relative
            self.archive(path)
            require(self.archives[str(path)]['sha256'] == expected, f'Unexpected r2 {relative}')
        baseline = self.base / 'Data/patch-T.MPQ'
        originals = {}
        for line in self.run('list', baseline).decode().splitlines():
            name, size = line.rsplit('\t', 1)
            if name.startswith('('):
                continue
            require(not name.startswith('File'), 'Unresolved r2 listfile entry')
            data = self.extract(baseline, name)
            require(len(data) == int(size), 'Incomplete r2 extraction')
            self.put(name, data)
            originals[normalize(name)] = sha(data)
        require(len(originals) == 30, 'Expected 30 r2 payload entries')
        snapshots = sorted(p for p in (self.w335 / 'Data').rglob('*')
                           if p.is_file() and p.suffix.lower() == '.mpq')
        require(snapshots, 'No 335 snapshot archives')
        self.audit_tables(snapshots)
        base_trs = self.extract(self.w335 / 'Data/patch-3.MPQ', TRS)
        base_wma = self.extract(self.w335 / 'Data/enUS/patch-enUS-N.MPQ', WMA)
        require(sha(base_trs) == TRS_HASH and sha(base_wma) == WMA_HASH, '335 baseline hash mismatch')
        patch9 = self.turtle / 'Data/patch-9.mpq'
        turtle_trs = parse_trs(self.extract(patch9, TRS))
        native_trs = parse_trs(base_trs)
        require(len(native_trs) == 18644, 'Unexpected 335 TRS mapping count')
        merged_wma, dbc_report = append_worldmap_area(base_wma, self.extract(patch9, WMA))
        require(dbc_report['rows_before'] == 212, 'Expected 212 baseline WorldMapArea rows')
        self.put(WMA, merged_wma)
        for i in range(1, 13):
            name = rf'Interface\WorldMap\KarazhanCrypt\KarazhanCrypt{i}.blp'
            data = self.extract(patch9, name)
            require(blp_dimensions(data) == [256, 256], 'Unexpected worldmap tile dimensions')
            self.put(name, data)
        texture_archives = [self.turtle / 'Data/patch.MPQ', self.turtle / 'Data/texture.MPQ']
        additions, terrain = [], []
        terrain_entries = sorted(v for k, v in turtle_trs.items() if k.startswith('karazhancrypt\\'))
        expected_terrain = {normalize(f'KarazhanCrypt\\map{x}_{y}.blp')
                            for x in (34, 35, 36) for y in (52, 53)}
        require({normalize(k) for k, _ in terrain_entries} == expected_terrain,
                'Unexpected Turtle terrain keys')
        for key, value in terrain_entries:
            info, data = self.turtle_image(value, [self.turtle / 'Data/texture.MPQ'])
            renamed = self.import_image(value, data, snapshots)
            additions.append((key, renamed))
            terrain.append(dict(key=key, target_value=renamed, **info))

        def family(prefix, archive):
            root = self.extract(archive, prefix + '.wmo')
            mohd = chunks(root)['MOHD']
            count = struct.unpack_from('<I', mohd, 4)[0]
            require(count == 19, 'Expected 19 WMO groups')
            groups = []
            for i in range(count):
                data = self.extract(archive, f'{prefix}_{i:03}.wmo')
                groups.append(dict(index=i, **group_header(data)))
            require(len({g['groupid'] for g in groups}) == count, 'Duplicate MOGP group ID')
            return groups

        targets = family(TARGET_WMO, baseline)
        sources = family(SOURCE_WMO, self.turtle / 'Data/wmo.MPQ')
        matched = match_groups(targets, sources)

        def images(table, index, native):
            pattern = re.compile(re.escape(normalize(NATIVE)) + rf'_{index:03}_(\d{{2}})_(\d{{2}})\.blp$')
            found = {}
            for canonical, (key, value) in table.items():
                match = pattern.fullmatch(canonical)
                if not match:
                    continue
                if native:
                    name = 'Textures\\Minimap\\' + value
                    data = self.extract(self.w335 / 'Data/common.MPQ', name)
                    info = dict(value=value, dimensions=blp_dimensions(data), sha256=sha(data),
                                archive=str(self.w335 / 'Data/common.MPQ'))
                else:
                    info, data = self.turtle_image(value, texture_archives)
                found[match.groups()] = dict(key=key, data=data, **info)
            return found

        groups, turtle_count, native_count = [], 0, 0
        for target, source in matched:
            native = images(native_trs, target['index'], True)
            turtle = images(turtle_trs, source['index'], False)
            reasons = hybrid_reasons(target, source, native, turtle)
            chosen = native if reasons else turtle
            require(native or not turtle, 'Turtle-only group images need explicit handling')
            image_report = []
            for grid, item in sorted(chosen.items()):
                key = f'{TARGET}_{target["index"]:03}_{grid[0]}_{grid[1]}.blp'
                if reasons:
                    value = item['value']
                    # Native alias must resolve unchanged even in higher snapshot patches.
                    for archive in snapshots + [self.base / p for p in R2_HASHES]:
                        override = self.extract(archive, 'Textures\\Minimap\\' + value, optional=True)
                        require(override is None or override == item['data'],
                                f'Native texture override differs: {archive}: {value}')
                    native_count += 1
                else:
                    value = self.import_image(item['value'], item['data'], snapshots)
                    turtle_count += 1
                additions.append((key, value))
                image_report.append(dict(key=key, value=value, grid=grid, sha256=item['sha256']))
            def public(items):
                return [{k: v for k, v in item.items() if k != 'data'}
                        for _, item in sorted(items.items())]
            groups.append(dict(target=target, turtle=source, selection='native' if reasons else
                               ('turtle' if chosen else 'no-group-minimap'), reasons=reasons,
                               native_images=public(native), turtle_images=public(turtle), aliases=image_report))
        fallbacks = [g['target']['index'] for g in groups if g['selection'] == 'native']
        require(fallbacks == [0, 2, 3, 9, 17], f'Unexpected hybrid fallback groups: {fallbacks}')
        require(turtle_count + native_count == 23, 'Expected 23 interior aliases')
        merged_trs = merge_trs(base_trs, additions)
        require(len(parse_trs(merged_trs)) == 18673, 'Expected 18673 final TRS mappings')
        self.put(TRS, merged_trs)
        manifest = self.out / 'patch.list'
        entries = sorted(self.payload.values(), key=lambda entry: normalize(entry[0]))
        manifest.write_text(''.join(f'{path}|{name}\n' for name, path in entries))
        final = self.out / 'Data/patch-T.MPQ'
        final.parent.mkdir()
        self.run('create', final, manifest)
        verify = self.out / 'roundtrip'
        verify.mkdir()
        verified = []
        for i, (name, path) in enumerate(entries):
            dest = verify / str(i)
            self.run('extract-one', final, name, dest)
            require(dest.read_bytes() == path.read_bytes(), f'MPQ roundtrip mismatch: {name}')
            verified.append(dict(member=name, sha256=file_sha(dest), size=dest.stat().st_size))
            if normalize(name) in originals:
                require(file_sha(dest) == originals[normalize(name)], 'Original r2 entry changed')
        listed = {normalize(line.rsplit('\t', 1)[0])
                  for line in self.run('list', final).decode().splitlines()
                  if not line.startswith('(')}
        require(listed == set(self.payload), 'MPQ payload inventory mismatch')
        for relative, expected in R2_HASHES.items():
            if relative == 'Data/patch-T.MPQ':
                continue
            dest = self.out / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.base / relative, dest)
            require(file_sha(dest) == expected, 'Z copy changed')
        # Check every probed input archive again, detecting accidental source writes/drift.
        for path, info in self.archives.items():
            require(file_sha(Path(path)) == info['sha256'], f'Input archive changed: {path}')
        report = dict(status='artifact-byte-validated; in-game untested', artifact=str(final),
                      patch_sha256=file_sha(final), baseline_r2=R2_HASHES,
                      unchanged_z={k: v for k, v in R2_HASHES.items() if 'patch-T' not in k},
                      input_archives=self.archives, sources=self.sources, table_override_audit=self.audit,
                      worldmap_area=dbc_report, worldmap_tiles=12, terrain=terrain, groups=groups,
                      fallback_groups=fallbacks, interior_turtle_aliases=turtle_count,
                      interior_native_aliases=native_count,
                      trs=dict(baseline_sha256=sha(base_trs), baseline_mappings=18644,
                               appended_mappings=len(additions), final_mappings=18673,
                               baseline_bytes_preserved=merged_trs.startswith(base_trs)),
                      original_entries_preserved_byteexact=len(originals), roundtrip_payloads=verified,
                      payload_entries=len(entries), input_archives_unchanged=True,
                      limitations=['Source directories are reference snapshots, not the active client.',
                                   'Client effective loading, world-map selection/player dot and minimap '
                                   'alignment require in-game validation.',
                                   'Hybrid fallback retains native art for incompatible groups; '
                                   'no WMO geometry or floor-routing tables are modified.'])
        (self.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({k: report[k] for k in ('artifact', 'patch_sha256', 'payload_entries',
                         'fallback_groups', 'interior_turtle_aliases', 'interior_native_aliases')}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'work/client-overlay-r3')
    parser.add_argument('--w335', type=Path, default=Path('/home/dev/wow-335'))
    parser.add_argument('--turtle', type=Path, default=Path('/home/dev/wow-turtle'))
    parser.add_argument('--base', type=Path, default=ROOT / 'work/client-overlay-r2')
    args = parser.parse_args()
    Builder(*(p.resolve() for p in (args.output, args.w335, args.turtle, args.base))).build()


if __name__ == '__main__':
    main()
