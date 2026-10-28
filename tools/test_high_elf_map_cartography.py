#!/usr/bin/env python3
"""Map0 cartography contracts with synthetic fixtures and pinned archive evidence."""
import argparse
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from dbc_write import write_dbc_bytes
from high_elf_map_cartography import (Builder, TILES, digest, file_hash,
                                      merge_overlays, normalize, overlay_delta,
                                      parse, region_lights, update_trs, CLICKMASK,
                                      CLICKMASK_CONFIG, merge_clickmask,
                                      native_wmo_minimap_prefix, regional_minimap_value)
from build_crypt_cartography import parse_trs
from high_elf_map_dbc import apply_delta, extract
import consolidate_client_patches as consolidation
import package_high_elf_map as package
from high_elf_interior_minimaps import PLAN, chunks


PREVIOUS_SOURCE = package.ROOT / 'client_patches/archive/high-elf-map-before-cartography-fix'


def previous_artifact(lock, relative):
    """Historical provenance paths can be mutable; resolve only pinned archive data."""
    pin = PREVIOUS_SOURCE / 'source-lock.json'
    if file_hash(pin) != lock['previous_regional_source_lock_sha256']:
        raise ValueError('Previous regional source lock drift')
    spec = json.loads(pin.read_text())['files'][relative]
    data = (PREVIOUS_SOURCE / relative).read_bytes()
    if digest(data) != spec['sha256'] or len(data) != spec['size']:
        raise ValueError('Previous regional artifact drift: ' + relative)
    return data


def assert_minimap_contract(case, report, baseline, result, artifact_path):
    """Exact ownership, including narrowly identified legacy aliases, not a prefix allowlist."""
    minimap = report['minimap']
    aliases = [a for w in minimap['interiors'] for a in w['aliases']]
    generated = minimap['generated_interiors']
    case.assertEqual(len(aliases), 11)
    case.assertEqual(len(generated), 11)
    families = [w for w in minimap['interiors'] if w['aliases']]
    case.assertEqual(len(families), 1)
    family = families[0]
    case.assertEqual(normalize(family['source']), 'world\\wmo\\outland\\nethermicros\\nethermicro_03.wmo')
    prefix = native_wmo_minimap_prefix(family['target'])
    legacy = []
    for alias in aliases:
        case.assertTrue(alias['target_key'].startswith(prefix + '_'))
        suffix = alias['target_key'][len(prefix):]
        case.assertEqual(normalize(alias['source_key']),
                         normalize(native_wmo_minimap_prefix(family['source']) + suffix))
        legacy.append(dict(alias, target_key=family['target'][:-4] + suffix))
    case.assertEqual(minimap['legacy_aliases_preserved'], [a['target_key'] for a in legacy])
    case.assertEqual(len(legacy), 11)
    plan = json.loads(PLAN.read_text())
    case.assertEqual(report['inputs']['interior-floor-plan']['sha256'], file_hash(PLAN))
    expected_generated = {'ter\\Custom\\HighElfMap\\' + g['file'] + '_001_00_00.blp': g
                          for g in plan['groups']}
    case.assertEqual({g['target_key'] for g in generated}, set(expected_generated))
    case.assertEqual(len({g['target_value'] for g in generated}), 7)
    for image in generated:
        spec = expected_generated[image['target_key']]
        for field in ('family', 'root_sha256', 'group_sha256'):
            case.assertEqual(image[field], spec[field])
        case.assertEqual(image['physical_name'], image['target_value'])
        case.assertEqual(image['group_index'], 1)
        case.assertEqual(image['grid'], [0, 0])
    images = [t['image'] for t in minimap['terrain']] + aliases + generated + legacy
    old, actual = parse_trs(baseline), parse_trs(result)
    updates = {normalize(i['target_key']): i for i in images}
    case.assertEqual(len(updates), 57)  # 24 terrain + 22 real interior lookups + 11 inert legacy keys.
    case.assertTrue(set(old) <= set(actual))
    case.assertEqual(set(actual) - set(old), set(updates) - set(old))
    for key, value in old.items():
        if key not in updates:
            case.assertEqual(actual[key], value, key)
    crypt = {k: v for k, v in old.items() if 'turtle800' in k or k.startswith('karazhancrypt\\')}
    case.assertEqual(len(crypt), 29)
    case.assertTrue(all(actual[k] == v for k, v in crypt.items()))
    for image in images:
        value = image['target_value']
        case.assertRegex(value, r'^[0-9a-f]{32}\.blp$')
        case.assertEqual(len(value.encode('ascii')), 36)
        data = artifact_path('Textures/Minimap/' + value).read_bytes()
        case.assertEqual(digest(data), image['sha256'])
        case.assertEqual(regional_minimap_value(data), value)
        case.assertEqual(actual[normalize(image['target_key'])][1], value)
    for image in legacy:
        key = normalize(image['target_key'])
        if key in old:
            case.assertIn(old[key][1], ('hemap_' + image['sha256'] + '.blp', image['target_value']))
        # Both legacy and native aliases must resolve to the exact same source image.
        native_key = normalize(image['target_key'][6:])
        case.assertEqual(actual[key][1], actual[native_key][1])
    return images


def overlay(identity, worldmap=509, area=5225, offset=1):
    return [identity, worldmap, area, 0, 0, 0, 0, 0, offset, 512, 256, 13, 27, 0, 0, 512, 256]


class TrsTests(unittest.TestCase):
    def setUp(self):
        self.base = (b'dir: Azeroth\r\nAzeroth\\map37_26.blp\tnative.blp\r\n'
                     b'Azeroth\\map40_40.blp\tkeep.blp\r\n'
                     b'dir: WMO\\Custom\\Turtle800\r\n'
                     b'WMO\\Custom\\Turtle800\\tw800crypt_000_00_00.blp\ttw800_x.blp')

    def test_only_selected_values_change_and_all_keys_survive(self):
        result = update_trs(self.base, [('azeroth/map37_26.BLP', 'hemap_new.blp'),
                                       ('Character\\Custom\\HighElfMap\\room_000_00_00.blp', 'inside.blp')])
        old, new = parse_trs(self.base), parse_trs(result)
        self.assertEqual(set(new) - set(old), {'character\\custom\\highelfmap\\room_000_00_00.blp'})
        for key in old:
            if key != 'azeroth\\map37_26.blp':
                self.assertEqual(new[key], old[key])
        self.assertIn(b'Azeroth\\map37_26.blp\themap_new.blp\r\n', result)
        self.assertIn(b'Azeroth\\map40_40.blp\tkeep.blp\r\n', result)

    def test_empty_update_is_byte_exact(self):
        self.assertEqual(update_trs(self.base, []), self.base)

    def test_rejects_duplicate_and_unsafe_updates(self):
        for updates in ([('A\\B.blp', 'x.blp'), ('a/b.BLP', 'y.blp')],
                        [('A\\B.blp', '../escape.blp')],
                        [('A\\B.blp', 'not-a-texture')]):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                update_trs(self.base, updates)

    def test_perimeter_is_exactly_23_plus_partial_tile(self):
        self.assertEqual(len(TILES), 24)
        self.assertIn((37, 26), TILES)
        self.assertNotIn((38, 25), TILES)
        self.assertNotIn((34, 22), TILES)


class OverlayTests(unittest.TestCase):
    def setUp(self):
        source = write_dbc_bytes(17, [overlay(999), overlay(13, worldmap=513, area=2040),
                                      overlay(800, worldmap=674, area=5086)], b'\0Art\0')
        self.delta = overlay_delta(source, {509: 509, 513: 513}, {5225: 5225, 2040: 2040})

    def test_scope_remaps_and_sort_based_allocation(self):
        rows, strings = parse(self.delta, 17)
        self.assertEqual([r[0] for r in rows], [60000, 60001])
        self.assertEqual([r[1] for r in rows], [513, 509])
        self.assertEqual(rows[1][9:], overlay(999)[9:])
        self.assertEqual(strings, b'\0Art\0Art\0')

    def test_rejects_external_area_reference(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            overlay_delta(write_dbc_bytes(17, [overlay(1, area=5086)], b'\0Art\0'),
                          {509: 509}, {5225: 5225})

    def test_rejects_missing_or_oversized_artwork(self):
        for col, value in ((8, 0), (9, 0), (10, 4097)):
            row = overlay(1)
            row[col] = value
            with self.subTest(col=col), self.assertRaises(ValueError):
                overlay_delta(write_dbc_bytes(17, [row], b'\0Art\0'), {509: 509}, {5225: 5225})

    def test_independent_baselines_keep_opaque_records_and_strings(self):
        outputs = []
        for text in (b'\0English\0Unused\0\xff\0', b'\0Espanol\0Unused\0', b'\0Server\0'):
            base = write_dbc_bytes(17, [overlay(22, worldmap=10, area=1)], text)
            result = merge_overlays(base, self.delta)
            rows, strings = parse(result, 17)
            self.assertEqual(result[20:88], base[20:88])
            self.assertTrue(strings.startswith(text))
            self.assertEqual(len(rows), 3)
            self.assertEqual(merge_overlays(result, self.delta), result)
            outputs.append(result)
        self.assertEqual(len(set(outputs)), 3)

    def test_id_and_natural_key_collisions_fail_closed(self):
        for row, text in ((overlay(60000, worldmap=9), b'\0Other\0'),
                          (overlay(3, worldmap=509), b'\0Other\0'),
                          (overlay(3, worldmap=509, area=123), b'\0Art\0')):
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, 'collision'):
                merge_overlays(write_dbc_bytes(17, [row], text), self.delta)

    def test_wrong_schema_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'schema'):
            merge_overlays(write_dbc_bytes(16, [[0] * 16], b'\0'), self.delta)


class LightTests(unittest.TestCase):
    def light(self, identity, x, z, radius=10, map_id=0):
        bits = struct.unpack('<5I', struct.pack('<5f', x * 36, 100 * 36, z * 36, 0, radius * 36))
        return [identity, map_id, *bits, 7, 8, 0, 0, 0]

    def test_converts_inches_and_includes_global_fallback(self):
        unit = 1600 / 3
        row = self.light(3, 37.5 * unit, 26.5 * unit)
        global_row = [1, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0]
        records = region_lights([global_row, row, self.light(5, 50 * unit, 50 * unit),
                                 self.light(9, 37.5 * unit, 26.5 * unit, map_id=1)])
        self.assertEqual([r['id'] for r in records], [1, 3])
        self.assertTrue(records[0]['global_fallback'])
        self.assertAlmostEqual(records[1]['adt_position_yards'][0], 20000)
        self.assertEqual(records[1]['radii_yards'], [0, 10])

    def test_rejects_invalid_radii(self):
        with self.assertRaisesRegex(ValueError, 'Light'):
            region_lights([self.light(5, 1, 1, radius=-1)])


class FakeSnapshot:
    root = Path('/synthetic')
    kind = 'fixture'

    def __init__(self, members):
        self.members = members

    def get(self, name):
        data = self.members.get(name)
        return None if data is None else (data, {'sha256': 'fixture'})


def minimap_blp(alpha=0, payload=b'12345678'):
    header = bytearray(148)
    header[:4] = b'BLP2'
    struct.pack_into('<I4B2I', header, 4, 1, 2, alpha, 0, 0, 4, 4)
    struct.pack_into('<I', header, 20, 148)
    struct.pack_into('<I', header, 84, len(payload))
    return bytes(header) + payload


class RegionalMinimapTests(unittest.TestCase):
    def test_short_identity_preserves_full_sha_and_alpha_dxt1(self):
        for alpha in (0, 1):
            data = minimap_blp(alpha)
            value = regional_minimap_value(data)
            self.assertEqual(value, digest(data)[:32] + '.blp')
            self.assertEqual(len(value), 36)
            self.assertEqual(value.encode()[:39], value.encode())
        invalid = bytearray(minimap_blp())
        invalid[10] = 7  # DXT5, not an accepted byte-exact DXT1 input.
        with self.assertRaisesRegex(ValueError, 'DXT1'):
            regional_minimap_value(bytes(invalid))

    def test_native_wmo_prefix_strips_six_even_for_character(self):
        self.assertEqual(native_wmo_minimap_prefix('World\\WMO\\Room.wmo'), 'WMO\\Room')
        self.assertEqual(native_wmo_minimap_prefix('Character\\Custom\\Room.WMO'), 'ter\\Custom\\Room')
        for name in ('a.wmo', 'abcdef.wmo', 'World\\Room.blp'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                native_wmo_minimap_prefix(name)

    def test_collisions_check_source_native_regular_and_output(self):
        data = minimap_blp()
        value = regional_minimap_value(data)
        source_member, target_member = 'Textures\\Minimap\\source.blp', 'Textures\\Minimap\\' + value
        mappings = {'azeroth\\map01_02.blp': ('Azeroth\\map01_02.blp', 'source.blp')}
        for conflicting in ('source', 'native', 'regular', 'output', None):
            with self.subTest(conflicting=conflicting), tempfile.TemporaryDirectory(dir='/tmp/opencode') as tmp:
                builder = Builder.__new__(Builder)
                builder.out, builder.files = Path(tmp), {}
                builder.inputs, builder.missing = {}, []
                builder.source = FakeSnapshot({source_member: data})
                builder.native = FakeSnapshot({})
                regular = FakeSnapshot({})
                if conflicting == 'output':
                    builder.put(target_member, b'collision', 'fixture')
                elif conflicting:
                    snap = {'source': builder.source, 'native': builder.native, 'regular': regular}[conflicting]
                    snap.members[target_member] = b'collision'
                if conflicting:
                    with self.assertRaisesRegex(ValueError, 'collision'):
                        builder.import_minimap_mapping(mappings, regular, 'Azeroth\\map01_02.blp', 'target.blp')
                else:
                    result = builder.import_minimap_mapping(mappings, regular, 'Azeroth\\map01_02.blp', 'target.blp')
                    self.assertEqual(result['sha256'], digest(data))
                    self.assertEqual((builder.out / 'files/Textures/Minimap' / value).read_bytes(), data)
                    # Identical output is safe to reuse.
                    builder.import_minimap_mapping(mappings, regular, 'Azeroth\\map01_02.blp', 'target.blp')

    def test_unselected_oversized_values_are_not_globally_rewritten(self):
        baseline = b'Azeroth\\map01_02.blp\told.blp\r\nOther\\map.blp\t' + b'x' * 64 + b'.blp\r\n'
        result = update_trs(baseline, [('Azeroth\\map01_02.blp', regional_minimap_value(minimap_blp()))])
        self.assertEqual(result.splitlines(keepends=True)[1], baseline.splitlines(keepends=True)[1])


class ClickmaskTests(unittest.TestCase):
    def setUp(self):
        base = [9876] * 16384
        source = [42] * 16384  # Unrelated Turtle geography must never leak.
        for x, y, old, new in ((74, 45, 214, 2040), (73, 49, 2037, 5225),
                                (72, 52, 28, 5225), (73, 52, 139, 5225)):
            base[y*128+x], source[y*128+x] = old, new
        self.baseline = struct.pack('<16384I', *base)
        self.source = struct.pack('<16384I', *source)
        self.config = {'source_sha256': digest(self.source), 'areas': [2040, 5225],
                       'source_cells': 4, 'ported_cells': 2, 'replaceable_areas': [214, 2037],
                       'retained_border': [{'x': 72, 'y': 52, 'area': 28}, {'x': 73, 'y': 52, 'area': 139}]}

    def test_minimal_diff_byte_exact_other_cells_and_idempotency(self):
        result, audit = merge_clickmask(self.baseline, self.source, self.config)
        self.assertEqual([(c['x'], c['y'], c['original_area'], c['new_area']) for c in audit['diff']],
                         [(74, 45, 214, 2040), (73, 49, 2037, 5225)])
        allowed = {45*128+74, 49*128+73}
        for i in range(16384):
            if i not in allowed:
                self.assertEqual(result[i*4:i*4+4], self.baseline[i*4:i*4+4])
        self.assertEqual(struct.unpack_from('<I', result, (45*128+74)*4)[0], 2040)
        self.assertEqual(audit['result_sha256'], digest(result))
        for row in audit['rows']:
            y = row['y']
            self.assertEqual(row['original_sha256'], digest(self.baseline[y*512:(y+1)*512]))
            self.assertEqual(row['new_sha256'], digest(result[y*512:(y+1)*512]))
        again, report = merge_clickmask(result, self.source, self.config)
        self.assertEqual(again, result)
        self.assertEqual(report['diff'], [])
        self.assertEqual(report['ported_cells'], 2)

    def test_conflicts_and_border_changes_fail_closed(self):
        for x, y, value in ((74, 45, 28), (73, 49, 2040), (72, 52, 214), (73, 52, 5225)):
            data = bytearray(self.baseline)
            struct.pack_into('<I', data, (y*128+x)*4, value)
            with self.subTest(x=x, y=y), self.assertRaisesRegex(ValueError, 'conflict'):
                merge_clickmask(bytes(data), self.source, self.config)

    def test_rejects_size_source_hash_and_selection_drift(self):
        for baseline, source, config in ((self.baseline[:-4], self.source, self.config),
                                          (self.baseline, self.source[:-4], self.config),
                                          (self.baseline, bytes(65536), self.config),
                                          (self.baseline, self.source, dict(self.config, source_cells=5)),
                                          (self.baseline, self.source, dict(self.config, ported_cells=3))):
            with self.assertRaises(ValueError):
                merge_clickmask(baseline, source, config)

    def test_regular_override_unknown_hash_rejected_and_known_result_reused(self):
        expected, _ = merge_clickmask(self.baseline, self.source, self.config)
        root = Path('/synthetic')
        archive = root / 'Data/patch-T.MPQ'
        for override in (b'unknown', self.baseline, expected):
            builder = Builder.__new__(Builder)
            builder.source = FakeSnapshot({CLICKMASK: self.source})
            builder.inputs, builder.missing, builder.report = {}, [], {'worldmap': {}}
            builder.args = argparse.Namespace(config={'area_ids': {'2040': 2040, '5225': 5225},
                                                      'stock_directory': '/stock'})
            regular = FakeSnapshot({})
            regular.archives = [archive]
            emitted = {}
            builder.put = lambda name, data, reason: emitted.update({name: data})
            config = dict(self.config, stock_archive='stock.MPQ', stock_sha256=digest(self.baseline),
                          source_archive='Data/patch-8.mpq')
            def extraction(path, member):
                return override if path == archive else (self.baseline if str(path).startswith('/stock') else self.source)
            with patch('high_elf_map_cartography.json.loads', return_value=config), \
                    patch('high_elf_map_cartography.file_hash', return_value='fixture'), \
                    patch('high_elf_map_cartography.extract', side_effect=extraction):
                if override == b'unknown':
                    with self.assertRaisesRegex(ValueError, 'Unknown regular clickmask'):
                        builder.clickmask(regular)
                else:
                    builder.clickmask(regular)
                    self.assertEqual(emitted[CLICKMASK], expected)


class AudioTests(unittest.TestCase):
    def builder(self):
        builder = Builder.__new__(Builder)
        builder.audio_cache, builder.inputs, builder.missing = {}, {}, []
        return builder

    def sound(self, identity=10, fields=29, advanced=0):
        row = [0] * fields
        row[0:4] = [identity, 1, 1, 6]
        row[13], row[23] = 1, 14
        if fields == 30:
            row[29] = advanced
        return write_dbc_bytes(fields, [row], b'\0Name\0one.ogg\0Sound\\Native\0')

    def snapshot(self, data, payload=b'actual sound'):
        members = {'DBFilesClient\\SoundEntries.dbc': data}
        if payload is not None:
            members['Sound\\Native\\one.ogg'] = payload
        return FakeSnapshot(members)

    def test_cross_version_sound_equivalence_includes_payload(self):
        builder = self.builder()
        source = builder.sound_semantic(self.snapshot(self.sound()), 'SoundEntries', 10)
        native = builder.sound_semantic(self.snapshot(self.sound(fields=30)), 'SoundEntries', 10)
        self.assertEqual(source, native)
        self.assertTrue(builder.resolved(source))
        different = builder.sound_semantic(self.snapshot(self.sound(fields=30), b'different'), 'SoundEntries', 10)
        self.assertNotEqual(source, different)

    def test_missing_custom_reference_or_payload_is_not_equivalent(self):
        builder = self.builder()
        for snap, identity in ((self.snapshot(self.sound()), 999),
                               (self.snapshot(self.sound(), None), 10)):
            result = builder.sound_semantic(snap, 'SoundEntries', identity)
            self.assertFalse(builder.resolved(result))

    def test_nonzero_wotlk_advanced_is_not_vanilla_equivalent(self):
        builder = self.builder()
        old = builder.sound_semantic(self.snapshot(self.sound()), 'SoundEntries', 10)
        new = builder.sound_semantic(self.snapshot(self.sound(fields=30, advanced=42)), 'SoundEntries', 10)
        self.assertNotEqual(old, new)
        self.assertFalse(builder.resolved(new))

    def test_unknown_audio_schema_fails_closed(self):
        builder = self.builder()
        with self.assertRaisesRegex(ValueError, 'audio schema'):
            builder.sound_semantic(self.snapshot(self.sound(fields=31)), 'SoundEntries', 10)

    def test_recursive_zone_music_detects_same_id_different_sound(self):
        builder = self.builder()
        source = self.snapshot(self.sound())
        native = self.snapshot(self.sound(fields=30), b'different music')
        zone = write_dbc_bytes(8, [[100, 1, 1, 1, 2, 2, 10, 10]], b'\0Zone\0')
        for snapshot in (source, native):
            snapshot.members['DBFilesClient\\ZoneMusic.dbc'] = zone
        self.assertNotEqual(builder.sound_semantic(source, 'ZoneMusic', 100),
                            builder.sound_semantic(native, 'ZoneMusic', 100))
        self.assertIsNone(builder.sound_semantic(native, 'ZoneMusic', 0))

    def test_neutralization_changes_only_new_rows(self):
        # Exercise full 22-area policy, not just the semantic helper.
        builder = self.builder()
        source_rows, target_rows = [], []
        for i in range(22):
            old, new = [0] * 25, [0] * 36
            old[0], old[8], old[11] = 100 + i, 9999, 1
            new[0], new[3], new[8], new[11] = 6500 + i, 3500 + i, 9999, 1
            source_rows.append(old)
            target_rows.append(new)
        donor = [0] * 36
        donor[0], donor[8] = 3430, 55
        zone = write_dbc_bytes(8, [[55, 1, 0, 0, 0, 0, 0, 0]], b'\0Eversong\0')
        empty = write_dbc_bytes(8, [], b'\0')
        source = FakeSnapshot({'DBFilesClient\\ZoneMusic.dbc': empty})
        native = FakeSnapshot({'DBFilesClient\\AreaTable.dbc': write_dbc_bytes(36, [donor], b'\0'),
                               'DBFilesClient\\ZoneMusic.dbc': zone,
                               'DBFilesClient\\Light.dbc': write_dbc_bytes(15, [], b'\0')})
        source.members['DBFilesClient\\Light.dbc'] = write_dbc_bytes(12, [], b'\0')
        builder.source, builder.native = source, native
        builder.args = argparse.Namespace(config={'area_ids': {str(100 + i): 6500 + i for i in range(22)}})
        builder.report = {}
        emitted = {}
        builder.put = lambda name, data, reason: emitted.update({name: data})
        deltas = {'AreaTable': write_dbc_bytes(36, target_rows, b'\0Area\0')}
        wmo = [0] * 28
        wmo[0:4] = [60000, 6000, 0, 0xffffffff]
        wmo[7], wmo[10] = 9999, 6500
        deltas['WMOAreaTable'] = write_dbc_bytes(28, [wmo], b'\0')
        builder.audio(write_dbc_bytes(25, source_rows, b'\0Area\0'), deltas)
        rows, _ = parse(deltas['AreaTable'], 36)
        self.assertEqual({r[8] for r in rows}, {55})
        self.assertEqual(len(builder.report['ambience']['areas']), 22)
        self.assertFalse(builder.report['ambience']['source_music_added'])
        wrows, _ = parse(deltas['WMOAreaTable'], 28)
        self.assertEqual(wrows[0][7], 55)
        self.assertEqual(wrows[0][10], 6500)
        self.assertEqual(len(builder.report['ambience']['wmo_rows']), 1)
        self.assertIn('deltas/WMOAreaTable.dbc', emitted)
        baseline = write_dbc_bytes(36, [donor], b'\0Unused Native\0')
        merged = apply_delta('AreaTable', baseline, deltas['AreaTable'])
        self.assertEqual(merged[20:164], baseline[20:164])
        self.assertTrue(parse(merged, 36)[1].startswith(b'\0Unused Native\0'))


class RealCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # load() checks the pinned lock, complete inventory and every payload hash.
        # Paths inside the historical evidence are provenance, never live inputs.
        cls.lock = package.load()
        cls.manifest = json.loads((package.SOURCE / 'evidence/cartography-manifest.json').read_text())

    @staticmethod
    def artifact_path(relative):
        parts = Path(relative).parts
        if parts[0] == 'deltas':
            return package.SOURCE / relative
        if parts[0] in ('enUS', 'esES'):
            table = Path(relative).stem
            locale = 'enUS' if table in ('WorldMapArea', 'WorldMapOverlay') else parts[0]
            return package.SOURCE / 'results' / locale / (table + '.dbc')
        return package.SOURCE / 'shared' / relative

    def test_pinned_artifact_hashes_and_scoped_resource_closure(self):
        report = self.manifest
        # The historical builder hash is covered by the pinned evidence hash;
        # current pure functions are exercised by the synthetic tests above.
        self.assertEqual(report['missing'], [])
        self.assertFalse(report['apply_ready'])
        self.assertEqual({tuple(t['tile']) for t in report['minimap']['terrain']}, TILES)
        self.assertEqual(len(report['ambience']['areas']), 22)
        self.assertEqual(len(report['ambience']['wmo_rows']), 18)
        self.assertEqual(report['worldmap']['overlay_rows'], 9)
        for entry in report['files']:
            if entry['path'].startswith('server/'):
                continue  # Server additive validation has its own test suite.
            path = self.artifact_path(entry['path'])
            self.assertEqual(file_hash(path), entry['sha256'], entry['path'])
            self.assertNotIn(path.suffix.lower(), ('.adt', '.wdt', '.wdl', '.wmo', '.m2', '.mp3', '.wav', '.ogg'))
        for area in report['ambience']['areas'] + report['ambience']['wmo_rows']:
            for reference in area['references']:
                self.assertTrue(Builder.resolved(reference['target_semantic']))

    def test_independent_client_dbc_baselines_reproduce_pinned_results(self):
        for profile in ('enUS', 'esES'):
            for name, fields in (('AreaTable', 36), ('WorldMapArea', 11), ('WorldMapOverlay', 17),
                                 ('WMOAreaTable', 28)):
                with self.subTest(profile=profile, table=name):
                    locale = 'enUS' if name in ('WorldMapArea', 'WorldMapOverlay') else profile
                    relative = 'baselines/' + locale + '/' + name + '.dbc'
                    edit = next(e for e in self.lock['edits'] if e.get('baseline') == relative)
                    baseline = (package.SOURCE / relative).read_bytes()
                    delta = (package.SOURCE / edit['delta']).read_bytes()
                    merge = merge_overlays if name == 'WorldMapOverlay' else lambda b, d: apply_delta(name, b, d)
                    merged = merge(baseline, delta)
                    expected = self.artifact_path(profile + '/DBFilesClient/' + name + '.dbc').read_bytes()
                    self.assertEqual(merged, expected)
                    self.assertEqual(digest(merged), edit['result_sha256'])
                    self.assertEqual(merge(merged, delta), merged)
                    old, strings = parse(baseline, fields)
                    new, actual_strings = parse(merged, fields)
                    additions, _ = parse(delta, fields)
                    self.assertEqual(len(new), len(old) + len(additions))
                    self.assertEqual(new[:len(old)], old)
                    self.assertEqual(merged[20:20 + len(old) * fields * 4], baseline[20:20 + len(old) * fields * 4])
                    self.assertTrue(actual_strings.startswith(strings))

    def test_complete_regular_trs_and_crypt_keys_preserved(self):
        native_lock = json.loads(consolidation.LOCK.read_text())
        spec = native_lock['sources'][consolidation.CRYPT]
        archive = consolidation.pinned_path(consolidation.CRYPT, spec)
        member = spec['members']['textures/minimap/md5translate.trs']
        baseline = extract(archive, member['name'])
        self.assertEqual(digest(baseline), member['sha256'])
        edit = next(e for e in self.lock['edits']
                    if e['member'].lower() == 'textures\\minimap\\md5translate.trs')
        self.assertEqual(digest(baseline), edit['previous_sha256'])
        result = self.artifact_path('Textures/Minimap/md5translate.trs').read_bytes()
        images = assert_minimap_contract(self, self.manifest, baseline, result, self.artifact_path)
        old, final = parse_trs(baseline), parse_trs(result)
        self.assertEqual(set(self.lock['trs_changed_keys']), {k for k in old if old[k] != final[k]})
        # Legacy permission is established from the independently pinned prior
        # edition, not merely from the new manifest declaring a key as owned.
        previous = previous_artifact(self.lock, 'shared/Textures/Minimap/md5translate.trs')
        before = parse_trs(previous)
        for item in images:
            if item['target_key'] in self.manifest['minimap']['legacy_aliases_preserved']:
                self.assertIn(before[normalize(item['target_key'])][1],
                              ('hemap_' + item['sha256'] + '.blp', item['target_value']))
        assert_minimap_contract(self, self.manifest, previous, result, self.artifact_path)


FINAL_CANDIDATE = os.environ.get('HIGH_ELF_CARTOGRAPHY_CANDIDATE')


class FinalMapsCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock = package.load()
        cls.candidate = Path(FINAL_CANDIDATE).resolve() if FINAL_CANDIDATE else None
        cls.report = json.loads((cls.candidate / 'manifest.json' if cls.candidate else
                                 package.SOURCE / 'evidence/cartography-manifest.json').read_text())

    @classmethod
    def artifact_path(cls, relative):
        return (cls.candidate / 'files' / relative if cls.candidate else
                RealCandidateTests.artifact_path(relative))

    def test_strict_candidate_hashes_and_geographic_dbc_unchanged(self):
        self.assertEqual(self.report['missing'], [])
        self.assertEqual(self.report['validation']['strict_closure'], 'PASS')
        for entry in self.report['files']:
            if entry['path'].startswith('server/') and not self.candidate:
                continue  # Durable server payload is validated by its own suite.
            self.assertEqual(file_hash(self.artifact_path(entry['path'])), entry['sha256'])
        # Existing WorldMapArea allocation/bounds are not part of this fix.
        previous = json.loads(previous_artifact(self.lock, 'evidence/cartography-manifest.json'))
        previous_hashes = {entry['path']: entry['sha256'] for entry in previous['files']}
        actual_hashes = {entry['path']: entry['sha256'] for entry in self.report['files']}
        for profile in ('enUS', 'esES', 'server', 'deltas'):
            relative = profile + ('/' if profile == 'deltas' else '/DBFilesClient/') + 'WorldMapArea.dbc'
            self.assertEqual(actual_hashes[relative], previous_hashes[relative])
            if profile != 'server' or self.candidate:
                self.assertEqual(file_hash(self.artifact_path(relative)), previous_hashes[relative])

    def test_real_clickmask_has_exactly_44_changes_and_two_native_border_cells(self):
        config = json.loads(CLICKMASK_CONFIG.read_text())
        stock_input = self.report['inputs']['stock-clickmask']
        source_input = self.report['inputs']['source-clickmask']
        self.assertEqual(self.report['inputs']['clickmask-config']['sha256'], file_hash(CLICKMASK_CONFIG))
        baseline = extract(Path(stock_input['archive']), CLICKMASK)
        source = extract(Path(source_input['archive']), CLICKMASK)
        self.assertEqual(digest(baseline), config['stock_sha256'])
        self.assertEqual(digest(source), config['source_sha256'])
        self.assertEqual(stock_input['sha256'], config['stock_sha256'])
        self.assertEqual(source_input['sha256'], config['source_sha256'])
        result, audit = merge_clickmask(baseline, source, config)
        self.assertEqual(self.artifact_path('Interface/WorldMap/Azeroth.zmp').read_bytes(), result)
        self.assertEqual(audit['source_cells'], 46)
        self.assertEqual(audit['changed_cells'], 44)
        self.assertEqual(audit['ported_cells'], 44)
        recorded = self.report['worldmap']['clickmask']
        effective = baseline
        if recorded['regular_overrides']:
            override = recorded['regular_overrides'][0]
            # Only these two known images are legal. Never reopen a historical
            # regular archive path that may have been republished since capture.
            effective = {digest(baseline): baseline, digest(result): result}[override['sha256']]
        effective_result, effective_audit = merge_clickmask(effective, source, config)
        self.assertEqual(effective_result, result)
        for field in ('diff', 'approved_cells', 'rows', 'baseline_sha256', 'result_sha256', 'changed_cells'):
            self.assertEqual(recorded[field], effective_audit[field])
        for cell in config['retained_border']:
            self.assertEqual(struct.unpack_from('<I', result, (cell['y']*128+cell['x'])*4)[0], cell['area'])
        changed = {(c['x'], c['y']) for c in audit['diff']}
        for i in range(16384):
            if (i % 128, i // 128) not in changed:
                self.assertEqual(result[i*4:i*4+4], baseline[i*4:i*4+4])

    def test_real_short_values_source_bytes_and_native_wmo_aliases(self):
        report = self.report
        previous = previous_artifact(self.lock, 'shared/Textures/Minimap/md5translate.trs')
        durable = RealCandidateTests.artifact_path('Textures/Minimap/md5translate.trs').read_bytes()
        known = {digest(previous): previous, digest(durable): durable}
        baseline = known[report['minimap']['baseline_sha256']]
        self.assertEqual(digest(baseline), report['minimap']['baseline_sha256'])
        merged = self.artifact_path('Textures/Minimap/md5translate.trs').read_bytes()
        images = assert_minimap_contract(self, report, baseline, merged, self.artifact_path)
        # Even a candidate based on an already integrated profile must preserve
        # the independent, pre-fix snapshot outside the exact approved keys.
        assert_minimap_contract(self, report, previous, merged, self.artifact_path)
        aliases = [a for w in report['minimap']['interiors'] for a in w['aliases']]
        for image in [t['image'] for t in report['minimap']['terrain']] + aliases:
            # Full-hash physical names in the immutable previous edition identify
            # the original source image independently of the current short name.
            original = previous_artifact(self.lock, 'shared/Textures/Minimap/hemap_' + image['sha256'] + '.blp')
            self.assertEqual(self.artifact_path('Textures/Minimap/' + image['target_value']).read_bytes(), original)
        self.assertEqual(merged, update_trs(baseline, [(i['target_key'], i['target_value']) for i in images]))

    def test_complete_custom_interior_coverage(self):
        assets = json.loads((package.SOURCE / 'evidence/assets-manifest.json').read_text())
        actual = parse_trs(self.artifact_path('Textures/Minimap/md5translate.trs').read_bytes())
        covered = set()
        minimap = self.report['minimap']
        images = [a for w in minimap['interiors'] for a in w['aliases']] + minimap['generated_interiors']
        self.assertEqual(len(images), 22)
        for image in images:
            key = normalize(image['target_key'])
            prefix, index, x, y = key[:-4].rsplit('_', 3)
            self.assertEqual((x, y), ('00', '00'))
            covered.add((prefix, int(index)))
            self.assertEqual(actual[key][1], image['target_value'])
        expected = set()
        for resource in assets['resources']:
            if resource['kind'] != 'wmo' or resource['status'] != 'staged':
                continue
            for index, group in enumerate(resource['groups']):
                member = resource['target'][:-4] + f'_{index:03}.wmo'
                raw = (package.SOURCE / 'shared' / member.replace('\\', '/')).read_bytes()
                self.assertEqual(digest(raw), group['provenance']['sha256'])
                if struct.unpack_from('<I', chunks(raw)['MOGP'], 8)[0] & 0x2000:
                    expected.add((normalize(native_wmo_minimap_prefix(resource['target'])), index))
        self.assertEqual(len(expected), 22)
        self.assertEqual(covered, expected)

    def test_native_interior_coverage_when_snapshot_fixtures_available(self):
        assets = json.loads((package.SOURCE / 'evidence/assets-manifest.json').read_text())
        resources = [r for r in assets['resources'] if r['kind'] == 'wmo' and r['status'] == 'native-reuse']
        if not all(Path(g['provenance']['archive']).is_file() for r in resources for g in r['groups']):
            self.skipTest('Optional native WMO snapshot fixtures unavailable')
        native_lock = json.loads(consolidation.LOCK.read_text())
        spec = native_lock['sources'][consolidation.CRYPT]
        member = spec['members']['textures/minimap/md5translate.trs']
        baseline = extract(consolidation.pinned_path(consolidation.CRYPT, spec), member['name'])
        self.assertEqual(digest(baseline), member['sha256'])
        old = parse_trs(baseline)
        actual = parse_trs(self.artifact_path('Textures/Minimap/md5translate.trs').read_bytes())
        interiors = 0
        for resource in resources:
            prefix = normalize(native_wmo_minimap_prefix(resource['target']))
            for index, group in enumerate(resource['groups']):
                provenance = group['provenance']
                raw = extract(Path(provenance['archive']), provenance['member'])
                self.assertEqual(digest(raw), provenance['sha256'])
                if not struct.unpack_from('<I', chunks(raw)['MOGP'], 8)[0] & 0x2000:
                    continue
                interiors += 1
                keys = [k for k in old if k.startswith(prefix + f'_{index:03}_')]
                self.assertTrue(keys, resource['target'] + f' group {index}')
                for key in keys:
                    self.assertEqual(actual[key], old[key])
        self.assertEqual(interiors, 57)


if __name__ == '__main__':
    unittest.main()
