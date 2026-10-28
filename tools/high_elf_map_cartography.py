#!/usr/bin/env python3
"""Offline cartography/ambience closure for HighElf Highlands and AlahThalas, Map0.

Writes a fresh work/ candidate, never a client archive or deployment. Uses the
asset builder's read-only Snapshot and persistent reader, without modifying it.
"""
import argparse
import json
import math
from pathlib import Path
import re
import struct

from build_crypt_cartography import (TRS, group_header, merge_trs, normalize,
                                    parse_trs, safe_relative)
from dbc_write import write_dbc_bytes
from high_elf_map_assets import (ROOT, Snapshot, build_reader, client_path, digest,
                                 file_hash, validate_blp)
from high_elf_map_dbc import (apply_delta, make_deltas, parse, require,
                              resolve_regular, string_at, extract)

TOKENS = {'AlahThalas', 'ThalassianHighlands'}
TILES = {(33, y) for y in range(22, 26)} | {(34, y) for y in range(23, 26)} | {
    (35, y) for y in range(23, 27)} | {(36, y) for y in range(22, 27)} | {
    (37, y) for y in range(22, 27)} | {(38, y) for y in range(22, 25)}
SOUND_STRINGS = {'SoundEntries': [2, *range(3, 13), 23], 'ZoneMusic': [1],
                 'ZoneIntroMusicTable': [1], 'SoundAmbience': [],
                 'SoundProviderPreferences': [1]}
SOUND_FIELDS = {'SoundEntries': (29, 30), 'ZoneMusic': (8,),
                'ZoneIntroMusicTable': (5,), 'SoundAmbience': (3,),
                'SoundProviderPreferences': (24,)}
AREA_AUDIO = {5: 'SoundProviderPreferences', 6: 'SoundProviderPreferences',
              7: 'SoundAmbience', 8: 'ZoneMusic', 9: 'ZoneIntroMusicTable'}
CLICKMASK = 'Interface\\WorldMap\\Azeroth.zmp'
CLICKMASK_CONFIG = ROOT / 'tools/high-elf-map-clickmask.json'


def native_wmo_minimap_prefix(target):
    """335 strips six path characters unconditionally, including Character\\."""
    target = client_path(target)
    require(target.lower().endswith('.wmo') and len(target[:-4]) > 6,
            'WMO path too short for native minimap prefix')
    return target[6:-4]


def regional_minimap_value(data):
    # TRSValueBuffer[40] copies at most 39 bytes, including the .blp suffix.
    # Keep the full SHA in evidence; truncated identities are collision checked.
    validate_blp(data)
    require(data[:4] == b'BLP2' and struct.unpack_from('<I', data, 4)[0] == 1 and
            data[8] == 2 and data[9] in (0, 1) and data[10] == 0,
            'Regional minimap must be native BLP2 DXT1')
    value = digest(data)[:32] + '.blp'
    require(len(value.encode('ascii')) <= 39, 'Regional TRS value exceeds client buffer')
    return value


def merge_clickmask(baseline, source, config):
    """Port only the audited click cells; x is the column, y the row (LE u32)."""
    require(len(baseline) == len(source) == 128 * 128 * 4, 'Invalid ZMP length')
    require(digest(source) == config['source_sha256'], 'Source clickmask drift')
    old = struct.unpack('<16384I', baseline)
    src = struct.unpack('<16384I', source)
    targets = set(config['areas'])
    selected = {i for i, area in enumerate(src) if area in targets}
    require(len(selected) == config['source_cells'], 'Source clickmask selection drift')
    retained = {cell['y'] * 128 + cell['x']: cell for cell in config['retained_border']}
    require(set(retained) <= selected, 'Missing clickmask border cells')
    result, changes, approved = bytearray(baseline), [], []
    for i in sorted(selected):
        x, y = i % 128, i // 128
        if i in retained:
            require(old[i] == retained[i]['area'], 'Clickmask border conflict')
            continue
        require(old[i] in config['replaceable_areas'] or old[i] == src[i],
                f'Clickmask conflict at ({x},{y}): {old[i]} -> {src[i]}')
        item = {'x': x, 'y': y, 'original_area': old[i], 'new_area': src[i]}
        approved.append(item)
        if old[i] != src[i]:
            changes.append(item)
        struct.pack_into('<I', result, i * 4, src[i])
    require(len(approved) == config['ported_cells'], 'Clickmask port count drift')
    result = bytes(result)
    changed = {i for i in range(16384) if baseline[i*4:i*4+4] != result[i*4:i*4+4]}
    require(changed == {c['y'] * 128 + c['x'] for c in changes}, 'Unselected ZMP cell changed')
    rows = sorted({c['y'] for c in approved})
    return result, {'member': CLICKMASK, 'layout': '128x128 uint32 little-endian; index=y*128+x',
                    'baseline_sha256': digest(baseline), 'source_sha256': digest(source),
                    'result_sha256': digest(result), 'source_cells': len(selected),
                    'ported_cells': len(approved), 'changed_cells': len(changes),
                    'diff': changes, 'approved_cells': approved,
                    'retained_border': config['retained_border'],
                    'other_cells_byteexact': True,
                    'rows': [{'y': y, 'original_sha256': digest(baseline[y*512:(y+1)*512]),
                              'new_sha256': digest(result[y*512:(y+1)*512])} for y in rows]}


def table(data):
    require(data is not None and len(data) >= 20, 'Missing/truncated DBC')
    fields = struct.unpack_from('<I', data, 8)[0]
    return parse(data, fields)


def update_trs(baseline, updates):
    """Keep the complete TRS, changing values only for explicitly selected keys."""
    original = parse_trs(baseline)
    canonical = {}
    for name, value in updates:
        k = normalize(client_path(name))
        require(k not in canonical, 'Duplicate TRS update: ' + name)
        # Reuse the strict parser for values and delimiters, too.
        parse_trs((name + '\t' + value + '\n').encode('ascii'))
        canonical[k] = (name, value)
    lines = []
    for line in baseline.decode('ascii').splitlines(keepends=True):
        if '\t' in line:
            name = line.split('\t')[0]
            k = normalize(name)
            if k in canonical:
                ending = '\r\n' if line.endswith('\r\n') else ('\n' if line.endswith('\n') else '')
                line = name + '\t' + canonical[k][1] + ending
        lines.append(line)
    merged = merge_trs(''.join(lines).encode('ascii'),
                       [v for k, v in canonical.items() if k not in original])
    actual = parse_trs(merged)
    require(set(original) <= set(actual), 'Lost baseline TRS keys')
    require(all(actual[k] == v for k, v in original.items() if k not in canonical),
            'Unselected TRS mapping changed')
    return merged


def overlay_delta(data, worldmap_ids, area_ids):
    """Vanilla and 335 overlays share the 17-field layout; relocate texture strings."""
    rows, strings = parse(data, 17)
    result, sb = [], bytearray(b'\0')
    for row in sorted(rows, key=lambda r: r[0]):
        if row[1] not in worldmap_ids:
            continue
        require(all(not a or a in area_ids for a in row[2:6]),
                'Overlay references area outside selected closure')
        name = string_at(strings, row[8])
        require(name and row[9] and row[10] and row[9] <= 4096 and row[10] <= 4096,
                'Invalid overlay artwork/size')
        new = list(row)
        # Dedicated candidate-only range, checked against each independent
        # baseline below. Source IDs collide with unrelated WotLK overlays.
        new[0] = 60000 + len(result)
        new[1] = worldmap_ids[row[1]]
        new[2:6] = [area_ids.get(a, 0) for a in row[2:6]]
        new[8] = len(sb)
        sb.extend(name + b'\0')
        result.append(new)
    return write_dbc_bytes(17, result, bytes(sb))


def merge_overlays(baseline, delta):
    rows, strings = parse(baseline, 17)
    additions, ds = parse(delta, 17)
    sb, pending = bytearray(strings), []
    for row in additions:
        text = string_at(ds, row[8])
        for old in rows + pending:
            same = old[:8] + old[9:] == row[:8] + row[9:] and string_at(bytes(sb), old[8]) == text
            if old[0] == row[0]:
                require(same, 'WorldMapOverlay ID collision')
            elif old[1] == row[1]:
                require(old[2:6] != row[2:6] and string_at(bytes(sb), old[8]) != text,
                        'WorldMapOverlay natural-key collision')
        if any(old[0] == row[0] for old in rows):
            continue
        new = list(row)
        new[8] = len(sb)
        sb.extend(text + b'\0')
        pending.append(new)
    return write_dbc_bytes(17, rows + pending, bytes(sb)) if pending else baseline


def region_lights(rows):
    """Light.dbc coordinates/radii are ADT-oriented inches (36 per yard).

    https://wowdev.wiki/DB/Light#LightRec::ConvertDBToGameCoords()
    Include Map0's global fallback as well as local spheres intersecting tiles.
    """
    records = []
    for row in rows:
        if row[1] != 0:
            continue
        x, y, z, inner, outer = struct.unpack('<5f', struct.pack('<5I', *row[2:7]))
        require(all(math.isfinite(v) for v in (x, y, z, inner, outer)) and
                0 <= inner <= outer, 'Invalid Light position/radii')
        x, y, z, inner, outer = (v / 36 for v in (x, y, z, inner, outer))
        global_light = x == y == z == inner == outer == 0
        # Conservative XZ sphere/rectangle intersection, independent of height.
        intersects = any(max(a * (1600 / 3) - x, 0, x - (a + 1) * (1600 / 3)) ** 2 +
                         max(b * (1600 / 3) - z, 0, z - (b + 1) * (1600 / 3)) ** 2 <= outer ** 2
                         for a, b in TILES)
        if global_light or intersects:
            records.append({'id': row[0], 'adt_position_yards': [x, y, z],
                            'radii_yards': [inner, outer], 'parameters': row[7:],
                            'global_fallback': global_light})
    return records


class Builder:
    def __init__(self, args):
        self.args = args
        self.out = args.output.resolve()
        require(self.out.is_relative_to((ROOT / 'work').resolve()) and
                self.out != (ROOT / 'work').resolve(), 'Output must be below work/')
        for path in (args.source, args.native, args.assets, args.dbc, args.terrain,
                     Path(args.config['server_directory']), ROOT / args.config['regular_directory']):
            path = path.resolve()
            require(not self.out.is_relative_to(path) and not path.is_relative_to(self.out),
                    'Inputs and output overlap')
        require(not self.out.exists(), 'Use a fresh output directory')
        self.out.mkdir(parents=True)
        evidence = self.out / 'evidence'
        evidence.mkdir()
        self.reader = build_reader(evidence)
        self.snapshots = []
        self.files, self.inputs, self.missing, self.audio_cache = {}, {}, [], {}
        self.report = {'schema': 1, 'map_id': 0, 'apply_ready': False,
                       'status': 'offline-cartography-candidate', 'files': [], 'missing': self.missing,
                       'baselines': {}}
        self.source = self.snapshot(args.source, 'turtle')
        self.native = self.snapshot(args.native, '335')

    def snapshot(self, root, kind, locale='esES'):
        snap = Snapshot(root, kind, self.out / 'evidence', ROOT / 'tools/mpq',
                        locale=locale, reader=self.reader)
        self.snapshots.append(snap)
        return snap

    def get(self, snapshot, name, required=True):
        found = snapshot.get(name)
        if found is None:
            if required:
                item = {'snapshot': str(snapshot.root), 'member': name,
                        'reason': 'missing after direct probing of every effective archive'}
                if item not in self.missing:
                    self.missing.append(item)
            return None
        data, provenance = found
        self.inputs[str(snapshot.root) + ':' + snapshot.kind + ':' + name] = provenance
        return data

    def put(self, name, data, reason):
        name = str(safe_relative(name))
        canonical = name.lower()
        if canonical in self.files:
            require(self.files[canonical]['sha256'] == digest(data), 'Output collision: ' + name)
            return
        path = self.out / 'files' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.files[canonical] = {'path': name, 'sha256': digest(data), 'bytes': len(data), 'reason': reason}

    def image(self, name):
        data = self.get(self.source, name)
        if data is not None:
            info = validate_blp(data)
            if re.search(r'(?:AlahThalas|ThalassianHighlands)\d+\.blp$', name):
                require((info['width'], info['height']) == (256, 256),
                        'Unexpected worldmap base tile dimensions')
            self.put(name, data, 'source artwork, no geometry')

    def regular(self, locale, name):
        data, archive = resolve_regular(self.args.config, locale, name)
        self.inputs[locale + '/' + name] = {'archive': str(archive), 'sha256': digest(data)}
        return data

    def worldmap(self):
        config = self.args.config
        sources = {name: self.get(self.source, 'DBFilesClient\\' + name + '.dbc')
                   for name in ('AreaTable', 'WMOAreaTable', 'WorldMapArea')}
        require(all(sources.values()), 'Missing geographic source DBC')
        for name, data in sources.items():
            require(digest(data) == config['source_sha256'][name], 'Source geographic DBC drift: ' + name)
        deltas, _ = make_deltas(config, sources)
        from high_elf_map_dbc import validate_assets_wmo
        self.report['placed_wmo_validation'] = validate_assets_wmo(deltas['WMOAreaTable'], self.args.assets)
        # The preceding stage is evidence, not an alternate source of row ownership.
        for name in deltas:
            path = self.args.dbc / 'deltas' / (name + '.dbc')
            require(path.read_bytes() == deltas[name], 'Geographic candidate delta drift: ' + name)
            self.inputs['dbc-delta/' + name] = {'path': str(path), 'sha256': file_hash(path)}
        rows, strings = parse(deltas['WorldMapArea'], 11)
        tokens = {string_at(strings, r[3]).decode('ascii') for r in rows}
        require(tokens == TOKENS and len(rows) == 2 and all(r[1] == 0 for r in rows),
                'Unexpected worldmap token/map closure')
        self.report['worldmap'] = {'tokens': sorted(tokens), 'rows': rows, 'artwork': []}
        for token in sorted(tokens):
            for index in range(1, 13):
                name = f'Interface\\WorldMap\\{token}\\{token}{index}.blp'
                self.image(name)
                self.report['worldmap']['artwork'].append(name)
            # Include source-owned auxiliary artwork (e.g. overview thumbnails).
            prefix = normalize(f'Interface\\WorldMap\\{token}\\')
            for name in sorted(self.source.index):
                if name.startswith(prefix) and name.endswith('.blp'):
                    self.image(name)
        overlay_source = self.get(self.source, 'DBFilesClient\\WorldMapOverlay.dbc')
        overlay = None if overlay_source is None else overlay_delta(
            overlay_source, {int(k): v for k, v in config['worldmap_ids'].items()},
            {int(k): v for k, v in config['area_ids'].items()})
        self.report['worldmap']['overlay_rows'] = None if overlay is None else len(parse(overlay, 17)[0])
        self.report['worldmap']['overlay_id_policy'] = '60000 + source-ID-sorted index, candidate-only; collision checked independently for server/enUS/esES'
        if overlay is not None:
            orows, os = parse(overlay, 17)
            source_overlays, _ = parse(overlay_source, 17)
            self.report['worldmap']['overlay_id_mapping'] = [
                {'source': old[0], 'target': new[0]} for old, new in zip(
                    sorted((r for r in source_overlays if str(r[1]) in config['worldmap_ids']),
                           key=lambda r: r[0]), orows)]
            by_id = {r[0]: string_at(strings, r[3]).decode('ascii') for r in rows}
            for row in orows:
                texture = string_at(os, row[8]).decode('ascii')
                # Native WorldMapFrame uses ceil(width/256)*ceil(height/256) pieces.
                for i in range(1, math.ceil(row[9] / 256) * math.ceil(row[10] / 256) + 1):
                    self.image(f'Interface\\WorldMap\\{by_id[row[1]]}\\{texture}{i}.blp')
            if orows:
                self.put('deltas/WorldMapOverlay.dbc', overlay, 'additive overlay rows')
        self.put('deltas/WorldMapArea.dbc', deltas['WorldMapArea'], 'geographic stage row contract')
        self.audio(sources['AreaTable'], deltas)
        for profile in ('server', 'enUS', 'esES'):
            for name in ('WorldMapArea', 'AreaTable', 'WMOAreaTable'):
                baseline = self.baseline(profile, name)
                merged = apply_delta(name, baseline, deltas[name])
                self.record_merge(profile, name, baseline, merged)
                self.put(f'{profile}/DBFilesClient/{name}.dbc', merged, 'independent additive baseline')
            if overlay is not None and parse(overlay, 17)[0]:
                baseline = self.baseline(profile, 'WorldMapOverlay')
                merged = merge_overlays(baseline, overlay)
                require(merge_overlays(merged, overlay) == merged, 'Non-idempotent overlay merge')
                self.record_merge(profile, 'WorldMapOverlay', baseline, merged)
                self.put(f'{profile}/DBFilesClient/WorldMapOverlay.dbc', merged,
                         'independent additive overlay baseline')

    def record_merge(self, profile, name, baseline, merged):
        old, strings = table(baseline)
        new, actual_strings = table(merged)
        require(new[:len(old)] == old and actual_strings.startswith(strings),
                'Baseline records/strings changed: ' + profile + '/' + name)
        self.report['baselines'].setdefault(profile, {})[name] = {
            'sha256': digest(baseline), 'rows_before': len(old), 'rows_after': len(new),
            'native_records_byteexact': True, 'native_strings_byteexact': True}

    def baseline(self, profile, name):
        if profile != 'server':
            return self.regular(profile, name)
        path = Path(self.args.config['server_directory']) / (name + '.dbc')
        data = path.read_bytes()
        self.inputs['server/' + name] = {'path': str(path), 'sha256': digest(data)}
        return data

    def sound_tables(self, snapshot, name):
        cache = (id(snapshot), name)
        if cache not in self.audio_cache:
            data = self.get(snapshot, 'DBFilesClient\\' + name + '.dbc')
            if data is not None:
                require(struct.unpack_from('<I', data, 8)[0] in SOUND_FIELDS[name],
                        'Unsupported audio schema: ' + name)
            self.audio_cache[cache] = table(data) if data is not None else ([], b'\0')
        rows, strings = self.audio_cache[cache]
        return {r[0]: r for r in rows}, strings

    def sound_semantic(self, snapshot, name, identity, trail=()):
        if not identity:
            return None
        require((name, identity) not in trail, 'Cyclic audio DBC reference')
        rows, strings = self.sound_tables(snapshot, name)
        row = rows.get(identity)
        if row is None:
            return {'unresolved': [name, identity]}
        value = list(row[1:])
        for col in SOUND_STRINGS[name]:
            value[col - 1] = string_at(strings, row[col]).decode('utf-8').replace('/', '\\').lower()
        links = {'ZoneMusic': (6, 7), 'SoundAmbience': (1, 2),
                 'ZoneIntroMusicTable': (2,)}.get(name, ())
        for col in links:
            value[col - 1] = self.sound_semantic(snapshot, 'SoundEntries', row[col],
                                                trail + ((name, identity),))
        if name == 'SoundEntries':
            # WotLK appends SoundEntriesAdvancedID; only zero is compatible.
            if len(row) == 30 and row[29]:
                return {'unresolved': ['SoundEntriesAdvanced', row[29]]}
            if len(row) == 30:
                value = value[:-1]
            paths = []
            directory = string_at(strings, row[23]).decode('utf-8')
            for col in range(3, 13):
                filename = string_at(strings, row[col]).decode('utf-8')
                if filename:
                    path = directory.rstrip('\\/') + '\\' + filename
                    data = self.get(snapshot, path, required=False)
                    paths.append({'path': normalize(path), 'sha256': digest(data) if data else None})
            return {'row': value, 'payloads': paths}
        return {'row': value}

    @staticmethod
    def resolved(value):
        if isinstance(value, dict):
            return 'unresolved' not in value and all(
                (v is not None if k == 'sha256' else Builder.resolved(v)) for k, v in value.items())
        if isinstance(value, list):
            return all(Builder.resolved(v) for v in value)
        return True

    def audio_references(self, src, target, columns, donor, donor_shift=0):
        refs = []
        for col, name in columns.items():
            identity = src[col]
            original = self.sound_semantic(self.source, name, identity)
            native = self.sound_semantic(self.native, name, identity)
            equivalent = self.resolved(original) and self.resolved(native) and original == native
            # Donor is AreaTable; WMOAreaTable's sound fields start one slot earlier.
            replacement = identity if equivalent else donor[col + donor_shift]
            final = self.sound_semantic(self.native, name, replacement)
            require(self.resolved(final), 'Unresolved native audio donor reference')
            target[col] = replacement
            refs.append({'field': col, 'table': name, 'source_id': identity,
                         'native_semantic_equal': equivalent, 'source_semantic': original,
                         'native_same_id_semantic': native, 'target_id': replacement,
                         'target_semantic': final,
                         'decision': 'preserve verified native equivalent' if equivalent else
                         'explicit neutralization to native Eversong Woods (3430)'})
        return refs

    def audio(self, source_area, deltas):
        source_rows, ss = parse(source_area, 25)
        source_rows = {r[0]: r for r in source_rows}
        native_area = self.get(self.native, 'DBFilesClient\\AreaTable.dbc')
        nr, ns = parse(native_area, 36)
        donor = next((r for r in nr if r[0] == 3430), None)
        require(donor is not None, 'Missing native Eversong Woods audio donor')
        rows, strings = parse(deltas['AreaTable'], 36)
        by_id = {r[0]: r for r in rows}
        audit = []
        for sid, tid in self.args.config['area_ids'].items():
            src = source_rows[int(sid)]
            target = by_id[tid]
            refs = self.audio_references(src, target, AREA_AUDIO, donor)
            audit.append({'source': int(sid), 'target': tid,
                          'name': string_at(ss, src[11]).decode('utf-8'), 'references': refs})
        require(len(audit) == 22, 'Expected exactly 22 new areas')
        deltas['AreaTable'] = write_dbc_bytes(36, rows, strings)
        self.put('deltas/AreaTable.dbc', deltas['AreaTable'], '22 areas with audited native-only audio')
        self.report['ambience'] = {'areas': audit, 'donor_area': 3430,
                                   'source_music_added': False,
                                   'policy': 'Reuse native semantic equivalents; unknown/different custom references use native Eversong Woods, no source music payloads.'}
        wmo_audit = []
        if 'WMOAreaTable' in deltas:
            wrows, ws = parse(deltas['WMOAreaTable'], 28)
            for row in wrows:
                wmo_audit.append({'target': row[0], 'wmo_root': row[1],
                                  'name_set': row[2], 'group_id': row[3],
                                  'references': self.audio_references(
                                      list(row), row, {c - 1: t for c, t in AREA_AUDIO.items()}, donor,
                                      donor_shift=1)})
            deltas['WMOAreaTable'] = write_dbc_bytes(28, wrows, ws)
            self.put('deltas/WMOAreaTable.dbc', deltas['WMOAreaTable'],
                     'selected WMO rows with audited native-only audio')
        self.report['ambience']['wmo_rows'] = wmo_audit
        # Light is positional on a continent, not an AreaTable foreign key.
        light = []
        for snapshot in (self.source, self.native):
            data = self.get(snapshot, 'DBFilesClient\\Light.dbc')
            if data is None:
                continue
            lr, _ = table(data)
            require(struct.unpack_from('<I', data, 8)[0] in (12, 15), 'Unsupported Light schema')
            light.append({'snapshot': str(snapshot.root),
                          'records_intersecting_region': region_lights(lr)})
        self.report['light'] = {'audit': light, 'imported': False,
                                'coordinate_reference': 'https://wowdev.wiki/DB/Light (ADT-oriented inches / 36)',
                                'decision': 'Retain native continent lighting; Turtle Light/LightParams/LightBand chains are not ported; visual parity NOT RUN.'}

    def import_minimap_mapping(self, source, regular, logical, target):
        entry = source.get(normalize(logical))
        if entry is None:
            self.missing.append({'member': logical, 'reason': 'source TRS key missing; no invented alias'})
            return None
        _, value = entry
        data = self.get(self.source, 'Textures\\Minimap\\' + value)
        if data is None:
            return None
        renamed = regional_minimap_value(data)
        member = 'Textures\\Minimap\\' + renamed
        for snapshot in (self.source, self.native, regular):
            old = self.get(snapshot, member, required=False)
            require(old is None or old == data, 'Minimap namespace collision')
        self.put(member, data, 'byte-exact native BLP2 DXT1 source minimap artwork')
        return {'source_key': logical, 'target_key': target, 'source_value': value,
                'target_value': renamed, 'sha256': digest(data), 'byteexact': True,
                'format': 'BLP2 DXT1'}

    def minimap(self):
        # Regular delivery supplies crypt's full TRS; stock official root archives
        # are only a fallback. Snapshot custom Z/M/N are never a fallback here.
        regular_root = (ROOT / self.args.config['regular_directory']).parent
        regular = self.snapshot(regular_root, 'regular')
        self.clickmask(regular)
        base = self.get(regular, TRS)
        require(base is not None, 'Missing regular/crypt TRS baseline')
        native = self.get(self.native, TRS)
        require(native is not None, 'Missing native TRS audit baseline')
        original, native_keys = parse_trs(base), parse_trs(native)
        require(set(native_keys) <= set(original), 'Regular TRS is not a complete native superset')
        crypt = {k: v for k, v in original.items() if 'turtle800' in k or k.startswith('karazhancrypt\\')}
        require(len(crypt) == 29, 'Expected 29 regular crypt mappings')
        source_data = self.get(self.source, TRS)
        require(source_data is not None, 'Missing source TRS')
        source = parse_trs(source_data)
        updates, terrain, interiors, legacy_aliases = [], [], [], []

        def import_mapping(logical, target):
            item = self.import_minimap_mapping(source, regular, logical, target)
            if item:
                updates.append((target, item['target_value']))
            return item

        terrain_manifest = self.args.terrain / 'manifest.json'
        if not terrain_manifest.is_file():
            terrain_manifest = self.args.terrain / 'report.json'
        terrain_report = json.loads(terrain_manifest.read_text())
        selection = {tuple(r['tile']): r['selected_source_cells'] for r in terrain_report['tiles']}
        require(set(selection) == TILES and len(TILES) == 24 and selection[(37, 26)] < 256,
                'Terrain selection differs from 23 + partial 37_26 contract')
        self.inputs['terrain-report'] = {'path': str(terrain_manifest),
                                         'sha256': file_hash(terrain_manifest)}
        for x, y in sorted(TILES):
            logical = f'Azeroth\\map{x:02}_{y:02}.blp'
            item = import_mapping(logical, logical)
            terrain.append({'tile': [x, y], 'selected_source_cells': selection[x, y],
                            'coverage': 'complete source 2D image; mixed terrain may differ; geometry unchanged',
                            'image': item})
        manifest_path = self.args.assets / 'manifest.json'
        assets = json.loads(manifest_path.read_text())
        self.inputs['assets-manifest'] = {'path': str(manifest_path), 'sha256': file_hash(manifest_path)}
        assets_files = {normalize(f['path']): f for f in assets['files']}
        for entry in assets['resources']:
            if entry['kind'] != 'wmo':
                continue
            source_prefix = native_wmo_minimap_prefix(entry['source'])
            target_prefix = native_wmo_minimap_prefix(entry['target'])
            keys = [v[0] for k, v in source.items() if k.startswith(normalize(source_prefix) + '_')]
            report = {'source': entry['source'], 'target': entry['target'],
                      'status': entry['status'], 'source_images': len(keys), 'aliases': []}
            interiors.append(report)
            if entry['status'] == 'native-reuse':
                report['decision'] = 'Keep native geometry/TRS; no source interior substitution'
                continue
            if entry['status'] != 'staged':
                report['decision'] = 'BLOCKED asset family; no speculative interior aliases'
                if keys:
                    self.missing.append({'member': entry['source'], 'reason': report['decision']})
                continue
            for logical in sorted(keys):
                suffix = logical[len(source_prefix):]
                match = re.fullmatch(r'_(\d{3})_(\d{2})_(\d{2})\.blp', suffix, re.I)
                require(match is not None, 'Unknown WMO minimap key layout')
                index = int(match[1])
                group = entry['target'][:-4] + f'_{index:03}.wmo'
                record = assets_files.get(normalize(group))
                require(record is not None, 'Unmanifested target WMO group')
                raw = (self.args.assets / 'files' / safe_relative(group)).read_bytes()
                require(digest(raw) == record['sha256'], 'Asset group hash drift')
                src_name = entry['source'][:-4] + f'_{index:03}.wmo'
                src = self.get(self.source, src_name)
                if src is None:
                    continue
                require(raw == src and group_header(raw) == group_header(src),
                        'Interior grid requires byte-exact source WMO group')
                alias = import_mapping(logical, target_prefix + suffix)
                if alias:
                    report['aliases'].append(alias)
                    # Earlier editions used the whole Character\... name as a
                    # key. Retain those inert aliases, but point them at the same
                    # short physical resource rather than an absent long name.
                    legacy = entry['target'][:-4] + suffix
                    old = original.get(normalize(legacy))
                    if old is not None and normalize(legacy) != normalize(target_prefix + suffix):
                        require(old[1] in ('hemap_' + alias['sha256'] + '.blp',
                                           alias['target_value']), 'Unknown legacy regional alias')
                        updates.append((legacy, alias['target_value']))
                        legacy_aliases.append(legacy)
            report['decision'] = 'Source grid aliases only for byte-exact staged source groups'
            if not keys:
                report['decision'] = 'No source TRS images for this family; no invented interior artwork'
        # These eleven interiors have no source/stock-equivalent artwork. Draw
        # their actual approved floor meshes, not a geometrically unrelated alias.
        from high_elf_interior_minimaps import PLAN as INTERIOR_PLAN, build_minimaps
        self.inputs['interior-floor-plan'] = {'path': str(INTERIOR_PLAN),
                                               'sha256': file_hash(INTERIOR_PLAN)}
        generated = []
        def native_texture(name):
            raw = self.get(self.native, name)
            require(raw is not None, 'Missing interior floor texture: ' + name)
            return raw
        for logical, (data, metadata) in sorted(build_minimaps(
                self.args.assets, native_resolver=native_texture).items()):
            name = regional_minimap_value(data)
            require(name == metadata['physical_name'], 'Interior physical name differs')
            member = 'Textures\\Minimap\\' + name
            require(normalize(logical) not in {normalize(k) for k, _ in updates},
                    'Generated interior collides with source artwork')
            for snapshot in (self.source, self.native, regular):
                old = self.get(snapshot, member, required=False)
                require(old is None or old == data, 'Interior minimap namespace collision')
            self.put(member, data, 'simplified floor plan rasterized from approved WMO geometry')
            updates.append((logical, name))
            generated.append(dict(metadata, target_key=logical, target_value=name))
        require(len(generated) == 11, 'Incomplete generated interior floor plans')
        terrain_keys = {normalize(f'Azeroth\\map{x:02}_{y:02}.blp') for x, y in TILES}
        legacy_keys = {normalize(k) for k in legacy_aliases}
        require(all(normalize(k) in terrain_keys or normalize(k) in legacy_keys or normalize(k) not in original or
                    original[normalize(k)][1] == v for k, v in updates),
                 'Isolated WMO TRS alias collision')
        merged = update_trs(base, updates)
        actual = parse_trs(merged)
        require(all(actual[k] == v for k, v in crypt.items()), 'Crypt mappings changed')
        self.put(TRS, merged, 'complete regular TRS; only selected terrain and isolated WMO aliases updated')
        self.report['minimap'] = {'terrain': terrain, 'interiors': interiors,
                                   'generated_interiors': generated,
                                   'legacy_aliases_preserved': legacy_aliases,
                                  'baseline_mappings': len(original), 'final_mappings': len(actual),
                                  'baseline_sha256': digest(base), 'crypt_mappings_preserved': len(crypt),
                                  'all_baseline_keys_preserved': True,
                                   'updates': len(updates)}

    def clickmask(self, regular):
        config_path = getattr(self.args, 'clickmask_config', CLICKMASK_CONFIG)
        config = json.loads(config_path.read_text())
        self.inputs['clickmask-config'] = {'path': str(config_path), 'sha256': file_hash(config_path)}
        require(set(config['areas']) == {2040, 5225} and all(
            self.args.config['area_ids'][str(a)] == a for a in config['areas']),
            'Clickmask area allocation drift')
        stock_archive = Path(self.args.config['stock_directory']) / config['stock_archive']
        stock = extract(stock_archive, CLICKMASK)
        require(stock is not None and digest(stock) == config['stock_sha256'],
                'Stock clickmask baseline drift')
        self.inputs['stock-clickmask'] = {'archive': str(stock_archive), 'member': CLICKMASK,
                                        'sha256': digest(stock), 'archive_sha256': file_hash(stock_archive)}
        source = self.get(self.source, CLICKMASK)
        require(source is not None, 'Missing source clickmask')
        source_archive = self.source.root / config['source_archive']
        require(extract(source_archive, CLICKMASK) == source, 'Source clickmask archive drift')
        self.inputs['source-clickmask'] = {'archive': str(source_archive), 'member': CLICKMASK,
                                         'sha256': digest(source), 'archive_sha256': file_hash(source_archive)}
        expected, _ = merge_clickmask(stock, source, config)
        baseline = stock
        # Root regular overrides are inputs too. Only the stock image or this
        # exact idempotent result is a known baseline; unknown edits fail closed.
        overrides = []
        for archive in regular.archives:
            if archive.parent != regular.root / 'Data':
                continue
            data = extract(archive, CLICKMASK)
            if data is None:
                continue
            require(data in (stock, expected), 'Unknown regular clickmask override: ' + str(archive))
            overrides.append({'archive': str(archive), 'member': CLICKMASK, 'sha256': digest(data)})
            if len(overrides) == 1:
                baseline = data
        result, audit = merge_clickmask(baseline, source, config)
        require(merge_clickmask(result, source, config)[0] == result, 'Non-idempotent clickmask')
        audit.update({'stock_sha256': digest(stock), 'regular_overrides': overrides})
        self.report['worldmap']['clickmask'] = audit
        self.put(CLICKMASK, result, '44 audited zone-click cells on stock/known regular baseline')

    def build(self):
        try:
            self.worldmap()
            self.minimap()
            require(all(file_hash(self.out / 'files' / f['path']) == f['sha256']
                        for f in self.files.values()), 'Output verification failed')
            self.report['files'] = sorted(self.files.values(), key=lambda f: f['path'].lower())
            self.report['inputs'] = self.inputs
            self.report['archives'] = {s.kind: s.provenance() for s in self.snapshots}
            self.report['closure_complete'] = not self.missing
            self.report['validation'] = {'offline_build': 'PASS',
                                         'strict_closure': 'FAIL' if self.missing else 'PASS',
                                         'client_render_and_map_alignment': 'NOT RUN',
                                         'server_runtime': 'NOT RUN', 'deployment': 'NOT PERFORMED'}
            self.report['limitations'] = [
                'Candidate only: geographic/terrain/assets stages retain their own unresolved gates.',
                'No continent WDL replacement: native distant horizon may omit the new region; regional WDL merge remains pending.',
                'Full source 2D minimap images include native-retained cells in mixed tiles, including 37_26; this does not modify geometry.',
                'Eleven interiors without source artwork use static simplified floor plans from their real WMO meshes; not Blizzard/Turtle artwork or dynamic multi-floor maps.',
                'Native positional lighting retained; custom light chains not imported. Native-only audio replaces unknown custom references.',
                'No source music, FrameXML, WDT, ADT, geometry or continent artwork replacement.',
                'World map player dot, overlays, WMO floor routing, minimap alignment and ambience require in-game validation.',
                'Locale DBC outputs are separate alternatives on independent baselines; root artwork/TRS is shared.']
            self.report['builder_sha256'] = file_hash(Path(__file__))
            (self.out / 'manifest.json').write_text(json.dumps(self.report, indent=2, ensure_ascii=False) + '\n')
            (self.out / 'CLOSURE.md').write_text(
                '# High-elf Map0 cartography candidate\n\n' +
                f'Strict resource closure: {self.report["validation"]["strict_closure"]}. '
                f'Missing: {len(self.missing)}. Apply-ready: false.\n\n' +
                '\n'.join('- ' + line for line in self.report['limitations']) + '\n\n'
                'See manifest.json for per-area audio decisions, selected tiles, WMO aliases, hashes and missing resources. '
                'No client or server files have been installed.\n')
            return self.report
        finally:
            for snapshot in self.snapshots:
                snapshot.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('/home/dev/wow-turtle'))
    parser.add_argument('--native', type=Path, default=Path('/home/dev/wow-335'))
    parser.add_argument('--assets', type=Path, default=ROOT / 'work/high-elf-assets-candidate')
    parser.add_argument('--dbc', type=Path, default=ROOT / 'work/high-elf-dbc-candidate')
    parser.add_argument('--terrain', type=Path, default=ROOT / 'work/high-elf-terrain-candidate')
    parser.add_argument('--output', type=Path, default=ROOT / 'work/high-elf-cartography-candidate')
    parser.add_argument('--config', type=Path, default=ROOT / 'tools/high-elf-map.json')
    parser.add_argument('--clickmask-config', type=Path, default=CLICKMASK_CONFIG)
    parser.add_argument('--strict', action='store_true', help='Exit nonzero after reporting any missing resources')
    args = parser.parse_args()
    args.config = json.loads(args.config.read_text())
    report = Builder(args).build()
    print(json.dumps({'output': str(args.output), 'files': len(report['files']),
                      'missing': len(report['missing']), 'validation': report['validation']}, indent=2))
    if args.strict and report['missing']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
