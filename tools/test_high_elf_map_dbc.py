#!/usr/bin/env python3
"""Synthetic checks plus local, read-only real-source/baseline integration.

    python3 -m unittest discover -s tools -p test_high_elf_map_dbc.py -v

Real-data tests skip when the proprietary source or baseline inputs are absent.
They never write deployed files or require a database. The builder separately
requires and records the read-only DEV SQL audit.
"""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import high_elf_map_dbc as h
from dbc_write import write_dbc_bytes


def dbc(fields, rows, strings=b'\0'):
    return write_dbc_bytes(fields, rows, strings)


def fixture():
    config = dict(map_id=0, roots=[2040, 5225],
                  area_ids={'2040': 2040, '5225': 5225, '3881': 6500},
                  explore_flags={'2040': 3500, '5225': 3501, '3881': 3502},
                  wmo_ids={'50301': 60000}, excluded_inherited_wmo_ids=[40976],
                  worldmap_ids={'509': 509})
    # Distinct numeric fields and all eight locales detect accidental shifting.
    strings = bytearray(b'\0')
    offsets = []
    for value in ['English', 'Korean', 'French', 'German', 'Chinese', 'Taiwanese',
                  'Español', 'Mexican', 'AlahThalas']:
        offsets.append(len(strings))
        strings.extend(value.encode() + b'\0')
    areas = []
    for aid, parent in [(2040, 0), (5225, 0), (3881, 5225)]:
        row = [aid, 0, parent, 1182, 312, 5, 6, 7, 8, 9, 10,
               *offsets[:8], 0x123456, 2, 0, 0xc59c4000, 0x3f000000, 24]
        areas.append(row)
    wmo = [50301, 6000, 0, 0xffffffff, 4, 5, 6, 7, 8, 9, 3881,
           *offsets[:8], 0xabcdef]
    inherited = [40976, 4772, 1, 0xffffffff, 0, 0, 0, 0, 0, 0, 3881,
                 *([0] * 8), 0]
    bounds = struct.unpack('<4I', struct.pack('<4f', 100, -100, 200, -200))
    wma = [509, 0, 2040, offsets[8], *bounds]
    sources = {'AreaTable': dbc(25, areas, strings),
               'WMOAreaTable': dbc(20, [inherited, wmo], strings),
               'WorldMapArea': dbc(8, [wma], strings)}
    return config, sources


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.config, self.sources = fixture()
        self.deltas, self.report = h.make_deltas(self.config, self.sources)

    def test_schema_conversion_and_locales(self):
        rows, strings = h.parse(self.deltas['AreaTable'], 36)
        area = next(r for r in rows if r[0] == 6500)
        self.assertEqual(area[:11], [6500, 0, 5225, 3502, 312, 5, 6, 7, 8, 9, 10])
        self.assertEqual([h.string_at(strings, i) for i in area[11:19]],
                         [s.encode() for s in ['English', 'Korean', 'French', 'German',
                                              'Chinese', 'Taiwanese', 'Español', 'Mexican']])
        self.assertEqual(area[19:27], [0] * 8)
        self.assertEqual(area[27:], [0x123456, 2, 0, 0, 0, 0,
                                     0xc59c4000, 0x3f000000, 24])
        rows, strings = h.parse(self.deltas['WMOAreaTable'], 28)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][:11], [60000, 6000, 0, 0xffffffff, 4, 5, 6, 7, 8, 9, 6500])
        self.assertEqual(rows[0][27], 0xabcdef)
        self.assertEqual(h.string_at(strings, rows[0][17]), 'Español'.encode())
        rows, strings = h.parse(self.deltas['WorldMapArea'], 11)
        original, _ = h.parse(self.sources['WorldMapArea'], 8)
        self.assertEqual(rows[0][4:8], original[0][4:8])
        self.assertEqual(rows[0][8:], [0xffffffff, 0, 0])
        self.assertEqual(h.string_at(strings, rows[0][3]), b'AlahThalas')
        self.assertEqual(len(self.report['excluded_wmo']), 1)

    def test_explicit_group_mapping_guards_source_identity(self):
        self.config['wmo_group_mappings'] = {'50301': dict(
            target_id=60000, root_id=6000, name_set=0,
            source_group=0xffffffff, target_group=0)}
        deltas, report = h.make_deltas(self.config, self.sources)
        self.assertEqual(h.parse(deltas['WMOAreaTable'], 28)[0][0][3], 0)
        self.assertEqual(report['wmo_group_mappings'][0]['source_id'], 50301)
        self.config['wmo_group_mappings']['50301']['source_group'] = 19746
        with self.assertRaisesRegex(ValueError, 'source identity changed'):
            h.make_deltas(self.config, self.sources)

    def test_placed_exact_group_and_nameset_no_wildcard_fallback(self):
        rows, strings = h.parse(self.deltas['WMOAreaTable'], 28)
        exact = rows[0].copy()
        exact[0], exact[3] = 60017, 19746
        bad = dbc(28, rows + [exact], strings)
        fixes = [dict(target_id=60017, root_id=6000, name_set=0, target_group=0)]
        with self.assertRaisesRegex(ValueError, 'exact group mismatch'):
            h.validate_placed_wmo(bad, [(6000, 0, [0])], fixes)
        exact[3] = 0
        good = dbc(28, rows + [exact], strings)
        self.assertEqual(h.validate_placed_wmo(good, [(6000, 0, [0, 99])])['checked_rows'],
                         [60000, 60017])  # No source metadata for group99: no invented row.
        with self.assertRaisesRegex(ValueError, 'nameSet'):
            h.validate_placed_wmo(good, [(6000, 1, [0])])
        # Different placed models can share a root/nameSet, with disjoint groups.
        h.validate_placed_wmo(good, [(6000, 0, [99]), (6000, 0, [0])])

    def test_fallback_does_not_invent_translation(self):
        rows, strings = h.parse(self.sources['AreaTable'], 25)
        rows[0][17] = 0
        self.sources['AreaTable'] = dbc(25, rows, strings)
        deltas, _ = h.make_deltas(self.config, self.sources)
        rows, strings = h.parse(deltas['AreaTable'], 36)
        self.assertEqual(h.string_at(strings, rows[0][17]), b'English')

    def test_unsupported_source_and_reservation_drift_rejected(self):
        for column, value in [(21, 1), (2, 999), (1, 530)]:
            with self.subTest(column=column):
                sources = self.sources.copy()
                rows, strings = h.parse(sources['AreaTable'], 25)
                rows[0][column] = value
                sources['AreaTable'] = dbc(25, rows, strings)
                with self.assertRaises(ValueError):
                    h.make_deltas(self.config, sources)
        for bits in [{'2040': 3500, '5225': 3500, '3881': 3502},
                     {'2040': 4096, '5225': 3501, '3881': 3502}]:
            with self.assertRaises(ValueError):
                h.make_deltas(dict(self.config, explore_flags=bits), self.sources)
        config = copy.deepcopy(self.config)
        config['area_ids']['9999'] = 9999
        config['explore_flags']['9999'] = 3503
        with self.assertRaisesRegex(ValueError, 'closure'):
            h.make_deltas(config, self.sources)

    def test_byteexact_native_records_and_idempotent_relocation(self):
        for table, (_, fields) in h.TABLES.items():
            with self.subTest(table=table):
                native = [0] * fields
                native[0] = 42
                native[3] = 1 if table == 'WorldMapArea' else 12
                if table == 'WMOAreaTable':
                    native[1] = 77
                baseline = dbc(fields, [native], b'\0native\0opaque\xff\0')
                merged = h.apply_delta(table, baseline, self.deltas[table])
                self.assertEqual(merged[20:20 + fields*4], baseline[20:20 + fields*4])
                _, before = h.parse(baseline, fields)
                _, after = h.parse(merged, fields)
                self.assertTrue(after.startswith(before))
                self.assertEqual(h.apply_delta(table, merged, self.deltas[table]), merged)

    def test_id_and_natural_key_collisions(self):
        for table, (_, fields) in h.TABLES.items():
            rows, strings = h.parse(self.deltas[table], fields)
            for collision in ('id', 'key'):
                with self.subTest(table=table, collision=collision):
                    native = rows[0].copy()
                    if collision == 'id':
                        native[4] ^= 1
                    else:
                        native[0] += 999
                    baseline = dbc(fields, [native], strings)
                    with self.assertRaisesRegex(ValueError, 'collision'):
                        h.apply_delta(table, baseline, self.deltas[table])
            # Also reject a duplicate key in a previously applied baseline.
            native = rows[0].copy()
            native[0] += 999
            with self.assertRaisesRegex(ValueError, 'collision'):
                h.apply_delta(table, dbc(fields, rows + [native], strings), self.deltas[table])

    def test_malformed_dbc_is_rejected(self):
        good = self.deltas['AreaTable']
        for bad in (b'', good[:-1], good+b'x', b'WDB2'+good[4:],
                    good[:12]+struct.pack('<I', 4)+good[16:]):
            with self.assertRaises(ValueError):
                h.parse(bad, 36)
        with self.assertRaises(ValueError):
            h.string_at(b'\0', 20)
        rows, strings = h.parse(good, 36)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            h.parse(dbc(36, rows + rows, strings), 36)

    def test_sql_override_guards(self):
        cases = [('AreaTable', dict(ID='123', AreaBit='3500', ParentAreaID='0')),
                 ('AreaTable', dict(ID='2040', AreaBit='0', ParentAreaID='0')),
                 ('WMOAreaTable', dict(ID='123', WMOID='6000', NameSetID='0', WMOGroupID='-1')),
                 ('WorldMapArea', dict(ID='123', MapID='0', AreaID='2040', AreaName='different')),
                 ('WorldMapArea', dict(ID='123', MapID='1', AreaID='12', AreaName='AlahThalas'))]
        for table, sql in cases:
            with self.subTest(table=table, sql=sql), self.assertRaises(ValueError):
                h.guard_overlays({table: {'rows': [sql]}}, self.deltas)


class RealDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((h.ROOT / 'tools/high-elf-map.json').read_text())
        directory = h.ROOT / cls.config['source_directory']
        if not all((directory / (t + '.dbc')).is_file() for t in h.TABLES):
            raise unittest.SkipTest('Local Turtle audit sources unavailable')
        cls.sources = {t: (directory / (t + '.dbc')).read_bytes() for t in h.TABLES}
        cls.deltas, cls.report = h.make_deltas(cls.config, cls.sources)

    def test_pinned_sources_and_all_22_bindings(self):
        for table, data in self.sources.items():
            self.assertEqual(h.sha(data), self.config['source_sha256'][table])
        self.assertEqual(len(self.report['areas']), 22)
        self.assertEqual([r['explore_flag'] for r in self.report['areas']], list(range(3500, 3522)))
        rows, _ = h.parse(self.deltas['AreaTable'], 36)
        ids = {r[0] for r in rows}
        self.assertFalse(ids & {3881, 3882, 3883})
        self.assertTrue({6500, 6501, 6502, 2040, 5225} <= ids)
        for row in rows:
            self.assertTrue(row[2] == 0 or row[2] in ids)
        self.assertEqual(len(self.report['excluded_wmo']), 13)
        rows, _ = h.parse(self.deltas['WMOAreaTable'], 28)
        self.assertEqual(len(rows), 18)
        self.assertEqual({r[1] for r in rows}, {6000, 6001, 6002})
        self.assertEqual({r[10] for r in rows}, {6500, 6501, 6502})
        rows, _ = h.parse(self.deltas['WorldMapArea'], 11)
        self.assertEqual({r[0] for r in rows}, {509, 513})
        self.assertEqual({r[2] for r in rows}, {2040, 5225})

    def test_source_locale_and_float_bytes_retained(self):
        for table, (old, new) in h.TABLES.items():
            source, ss = h.parse(self.sources[table], old)
            target, ts = h.parse(self.deltas[table], new)
            ids = h.mapping(self.config, 'area_ids' if table == 'AreaTable' else
                            'wmo_ids' if table == 'WMOAreaTable' else 'worldmap_ids')
            by_id = {r[0]: r for r in target}
            for row in source:
                if row[0] not in ids:
                    continue
                actual = by_id[ids[row[0]]]
                if table == 'WorldMapArea':
                    self.assertEqual(actual[4:8], row[4:8])
                    self.assertEqual(h.string_at(ts, actual[3]), h.string_at(ss, row[3]))
                else:
                    for i in range(8):
                        expected = h.string_at(ss, row[11+i])
                        if i == 6 and not expected:
                            expected = h.string_at(ss, row[11])
                        self.assertEqual(h.string_at(ts, actual[11+i]), expected)

    def test_independent_real_baselines_preserved_and_rerunnable(self):
        for profile in ('server', 'enUS', 'esES'):
            for table, (_, fields) in h.TABLES.items():
                with self.subTest(profile=profile, table=table):
                    if profile == 'server':
                        path = h.ROOT / 'dbc' / (table + '.dbc')
                        if not path.is_file():
                            self.skipTest('Local server DBC unavailable')
                        baseline = path.read_bytes()
                    else:
                        locale = 'enUS' if table == 'WorldMapArea' else profile
                        path = h.ROOT / 'client_patches/archive/source-inputs/high-elf-map/baselines' / locale / (table + '.dbc')
                        if not path.is_file():
                            self.skipTest('Local regular client unavailable')
                        baseline = path.read_bytes()
                    merged = h.apply_delta(table, baseline, self.deltas[table])
                    rows, strings = h.parse(baseline, fields)
                    actual, actual_strings = h.parse(merged, fields)
                    added, _ = h.parse(self.deltas[table], fields)
                    self.assertEqual(len(actual), len(rows) + len(added))
                    self.assertEqual(merged[20:20+len(rows)*fields*4],
                                     baseline[20:20+len(rows)*fields*4])
                    self.assertTrue(actual_strings.startswith(strings))
                    self.assertEqual(h.apply_delta(table, merged, self.deltas[table]), merged)
                    if table == 'AreaTable':
                        self.assertTrue({3881, 3882, 3883} <= {r[0] for r in rows})
                    if table == 'WMOAreaTable':
                        # Native Netherstorm routing is retained, never repointed.
                        by_id = {r[0]: r for r in actual}
                        for excluded in self.report['excluded_wmo']:
                            self.assertEqual(by_id[excluded[0]][:11], excluded)

    def test_final_assets_and_inn_exact_key(self):
        rows, _ = h.parse(self.deltas['WMOAreaTable'], 28)
        by_id = {r[0]: r for r in rows}
        self.assertEqual(by_id[60016][1:4], [6002, 0, 0xffffffff])
        self.assertEqual(by_id[60017][1:4], [6002, 0, 0])
        assets = h.ROOT / self.config['assets_directory']
        if not assets.is_dir():
            self.skipTest('Final assets unavailable')
        report = h.validate_assets_wmo(self.deltas['WMOAreaTable'], assets)
        self.assertIn(60017, report['checked_rows'])
        self.assertEqual(report['unused_source_rows'], [60014])

    def test_previous_owned_inn_row_requires_explicit_migration(self):
        from package_high_elf_map import merge
        delta = self.deltas['WMOAreaTable']
        rows, strings = h.parse(delta, 28)
        next(r for r in rows if r[0] == 60017)[3] = 19746
        installed_v1 = dbc(28, rows, strings)
        for apply in (h.apply_delta, merge):
            with self.subTest(merge=apply.__module__), self.assertRaisesRegex(ValueError, 'ID collision: 60017'):
                apply('WMOAreaTable', installed_v1, delta)


if __name__ == '__main__':
    unittest.main()
