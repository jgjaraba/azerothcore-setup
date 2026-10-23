"""Unit tests; set FOREST_TROLL_INTEGRATION=1 for two pinned-client builds.

python3 -m unittest discover -s tools -p 'test_forest_troll_skins.py' -v
FOREST_TROLL_INTEGRATION=1 python3 -m unittest discover -s tools -p 'test_forest_troll_skins.py' -v
"""
import json
import os
from pathlib import Path
import struct
import tempfile
import time
import unittest

import build_forest_troll_skins as forest


def encode(rows, strings=b'\0'):
    return (struct.pack('<4s4I', b'WDBC', len(rows), 10, 40, len(strings))
            + b''.join(struct.pack('<10I', *r) for r in rows) + strings)


def source_fixture():
    strings = bytearray(b'\0')
    rows = []
    for sex in (0, 1):
        label = ('Male', 'Female')[sex]
        for base in (0, 1, 4):
            for var in (range(5 + sex) if base == 1 else (0,)):
                for color in range(6, 12):
                    names = [f'ForestTroll{label}Skin00_{color - 6:02}.blp', '', '']
                    if base == 1:
                        names[:2] = [f'ForestTroll{label}Face{half}{var:02}_{color - 6:02}.blp'
                                     for half in ('Lower', 'Upper')]
                    if base == 4:
                        names[:2] = [f'ForestTroll{label}NakedPelvisSkin00_{color - 6:02}.blp',
                                     f'ForestTroll{label}NakedTorsoSkin00_{color - 6:02}.blp' if sex else '']
                    refs = []
                    for name in names:
                        if not name:
                            refs.append(0)
                        else:
                            refs.append(len(strings))
                            strings.extend(f'Character\\Troll\\{label}\\{name}'.encode() + b'\0')
                    rows.append((1000 + len(rows), 8, sex, base, var, color, *refs, 0))
    return rows, bytes(strings)


def blp1():
    # 4x4 indexed color, zero alpha, one mip.
    return (b'BLP1' + struct.pack('<6I', 1, 0, 4, 4, 5, 0)
            + struct.pack('<16I', 1180, *([0] * 15))
            + struct.pack('<16I', 16, *([0] * 15)) + bytes(1024 + 16))


class ForestTrollTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(forest.MANIFEST.read_text())
        self.source_rows, self.source_strings = source_fixture()
        self.selected = forest.select_source(self.source_rows, self.source_strings)
        self.delta = forest.make_delta(self.selected, self.manifest)

    def test_distinct_source_and_native_layouts(self):
        strings = b'\0body\0face\0extra\0'
        turtle = (7, 8, 1, 4, 2, 9, 1, 6, 11, 0)
        native = (7, 8, 1, 4, 1, 6, 11, 0, 2, 9)
        self.assertEqual(forest.decode(turtle, strings, 'turtle'), forest.decode(native, strings))
        self.assertNotEqual(forest.decode(turtle, strings), forest.decode(native, strings))

    def test_malformed_dbc_and_string_offsets_fail(self):
        for raw in (b'', encode([])[:-1], encode([]) + b'x', b'XXXX' + encode([])[4:]):
            with self.assertRaises(ValueError):
                forest.read_dbc(raw)
        for strings, offset in ((b'\0x', 1), (b'\0', 1), (b'\0', -1)):
            with self.assertRaises(ValueError):
                forest.text(strings, offset)
        with self.assertRaises(ValueError):
            forest.decode((0,) * 10, b'\0', 'unknown')

    def test_complete_families_and_target_allocation(self):
        self.assertEqual(len(self.delta), 90)
        self.assertEqual({r[0] for r in self.delta}, set(range(20000, 20090)))
        self.assertEqual({r[9] for r in self.delta}, set(range(18, 24)))
        self.assertEqual({r[7] for r in self.delta}, {0x11})
        self.assertEqual(sum(r[2] == 0 for r in self.delta), 42)
        self.assertEqual(sum(r[2] == 1 for r in self.delta), 48)
        self.assertEqual({r[8] for r in self.delta if r[2] == 0 and r[3] == 1}, set(range(5)))
        self.assertEqual({r[8] for r in self.delta if r[2] == 1 and r[3] == 1}, set(range(6)))
        self.assertTrue(all(n.startswith('Character\\Custom\\TurtleForestTroll\\')
                            for r in self.delta for n in r[4:7] if n))

    def test_missing_duplicate_wrong_flag_or_face_family_rejected(self):
        variants = [self.source_rows[:-1], self.source_rows + [self.source_rows[0]]]
        for index, value in ((9, 1), (4, 30), (5, 12)):
            changed = list(self.source_rows[0])
            changed[index] = value
            variants.append([tuple(changed)] + self.source_rows[1:])
        for rows in variants:
            with self.assertRaises(ValueError):
                forest.select_source(rows, self.source_strings)

    def test_preserves_baseline_bytes_strings_and_dk_npc_slots(self):
        # Deliberately unsorted baseline, including NPC colors and DK special faces.
        native = [(10, 8, 1, 1, 1, 0, 0, 5, 11, 17),
                  (11, 8, 0, 0, 1, 0, 0, 8, 0, 14),
                  (12, 8, 0, 1, 1, 0, 0, 5, 9, 15),
                  (13, 1, 0, 0, 1, 0, 0, 17, 0, 0)]
        prefix = b'\0old-texture\0unreferenced-byte-prefix\0'
        raw, dupes = forest.merge(native, prefix, self.delta)
        rows, strings = forest.read_dbc(raw)
        self.assertTrue(strings.startswith(prefix))
        self.assertEqual({r[0]: r for r in rows if r[0] < 20000}, {r[0]: r for r in native})
        self.assertEqual([forest.key(r) for r in rows], sorted(forest.key(r) for r in rows))
        self.assertEqual(dupes, [])
        self.assertEqual([forest.decode(r, strings) for r in rows if r[0] >= 20000], self.delta)

    def test_id_collisions_at_both_boundaries_rejected(self):
        for ident in (20000, 20089):
            with self.assertRaisesRegex(ValueError, 'Occupied native ID'):
                forest.merge([(ident, 1, 0, 0, 0, 0, 0, 17, 0, 0)], b'\0', self.delta)
        bad = self.delta[:-1] + [self.delta[0]]
        with self.assertRaisesRegex(ValueError, 'Duplicate delta IDs'):
            forest.merge([], b'\0', bad)

    def test_tuple_collision_ignores_flags_and_id(self):
        r = self.delta[0]
        native = (123, *r[1:4], 0, 0, 0, 8, *r[8:])
        with self.assertRaisesRegex(ValueError, 'Occupied native tuple'):
            forest.merge([native], b'\0', self.delta)
        changed = (20999, *r[1:7], 5, *r[8:])
        with self.assertRaisesRegex(ValueError, 'Duplicate delta tuple'):
            forest.merge([], b'\0', self.delta + [changed])

    def test_existing_baseline_duplicate_tuple_preserved_and_reported(self):
        a = (1, 1, 0, 0, 0, 0, 0, 17, 0, 0)
        b = (2, *a[1:7], 5, *a[8:])
        raw, dupes = forest.merge([a, b], b'\0', self.delta)
        self.assertEqual(forest.read_dbc(raw)[0][:2], [a, b])
        self.assertEqual(dupes, [{'key': [1, 0, 0, 0, 0], 'count': 2}])

    def test_blp1_mips_and_corruption(self):
        raw = blp1()
        self.assertEqual(forest.validate_blp(raw)['mips'][0]['bytes'], 16)
        for offset, value in ((12, 0), (28, len(raw) + 1), (92, 300)):
            bad = bytearray(raw)
            struct.pack_into('<I', bad, offset, value)
            with self.assertRaises(ValueError):
                forest.validate_blp(bad)
        with self.assertRaises(ValueError):
            forest.validate_blp(raw[:-1])

    def test_blp2_bounds_and_empty_eof_mip(self):
        raw = (b'BLP2' + struct.pack('<I4B2I', 1, 2, 0, 0, 1, 4, 4)
               + struct.pack('<16I', 148, 156, *([0] * 14))
               + struct.pack('<16I', 8, *([0] * 15)) + bytes(8))
        self.assertEqual(forest.validate_blp(raw)['magic'], 'BLP2')
        for bad in (raw[:-1], raw[:4] + bytes(len(raw) - 4)):
            with self.assertRaises(ValueError):
                forest.validate_blp(bad)

    def test_sql_guarded_apply_and_explicit_rollback(self):
        apply = forest.render_sql(self.delta)
        rollback = forest.render_sql(self.delta, rollback=True)
        self.assertNotIn('DELETE', apply)
        self.assertNotIn('REPLACE', apply)
        self.assertNotIn('ON DUPLICATE', apply)
        self.assertNotIn('DROP PROCEDURE IF EXISTS', apply)
        self.assertIn('WHERE a.`Id` IS NULL', apply)
        self.assertIn('DELETE a FROM `charsections_dbc` a JOIN', rollback)
        for sql in (apply, rollback):
            self.assertIn('ROLLBACK; RESIGNAL;', sql)
            self.assertIn('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE', sql)
            self.assertIn('BINARY a.`TexturePath1` <=> BINARY e.`TexturePath1`', sql)
            self.assertIn('a.`Flags` <=> e.`Flags`', sql)
            self.assertIn('semantic tuple occupied', sql)
            guard = sql[sql.index('ON a.`Race`'):sql.index("MESSAGE_TEXT = 'ForestTroll: semantic")]
            self.assertNotIn('Flags', guard)
            self.assertLess(sql.index('START TRANSACTION'), sql.index('owned ID has different fields'))
            self.assertLess(sql.index('owned ID has different fields'), sql.index('  COMMIT;'))
        self.assertEqual(forest.sql_value('a\\b'), "CONVERT(X'615c62' USING utf8mb4)")

    def test_apply_migrates_myisam_before_row_transaction_only(self):
        sql = forest.render_sql(self.delta)
        self.assertIn("AND ENGINE IN ('InnoDB', 'MyISAM')", sql)
        self.assertIn('target must be InnoDB or MyISAM', sql)
        self.assertLess(sql.index("AND ENGINE IN ('InnoDB', 'MyISAM')"),
                        sql.index('CREATE TEMPORARY TABLE'))
        migration = sql[sql.index("  IF EXISTS (SELECT 1 FROM information_schema.TABLES"):]
        self.assertIn("AND ENGINE = 'MyISAM') THEN", migration)
        self.assertEqual(sql.count('ALTER TABLE `charsections_dbc` ENGINE=InnoDB;'), 1)
        self.assertLess(sql.index('INSERT INTO `forest_troll_skins_expected`'),
                        sql.index('ALTER TABLE `charsections_dbc`'))
        self.assertLess(sql.index('ALTER TABLE `charsections_dbc`'),
                        sql.index('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE'))
        self.assertLess(sql.index('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE'),
                        sql.index('START TRANSACTION'))
        self.assertIn('ALTER privilege', sql)
        self.assertIn('NOT transactional', sql)
        self.assertIn('persists after rollback', sql)

    def test_rollback_requires_innodb_and_retains_structural_migration(self):
        sql = forest.render_sql(self.delta, rollback=True)
        self.assertIn("AND ENGINE = 'InnoDB') THEN", sql)
        self.assertIn('target must be InnoDB', sql)
        self.assertNotIn('MyISAM', sql)
        self.assertNotIn('ALTER TABLE', sql)
        self.assertIn('never converts the engine back', sql)
        self.assertLess(sql.index("AND ENGINE = 'InnoDB') THEN"),
                        sql.index('START TRANSACTION'))


@unittest.skipUnless(os.environ.get('FOREST_TROLL_INTEGRATION') == '1', 'opt-in pinned reference clients')
class PinnedClientIntegration(unittest.TestCase):
    def test_two_fresh_builds_identical_and_publishable(self):
        with tempfile.TemporaryDirectory(prefix='forest-integration-') as temp:
            a, b = Path(temp) / 'first', Path(temp) / 'second'
            first = forest.build(a)
            time.sleep(1.1)
            second = forest.build(b)
            self.assertEqual(first, second)
            for name in ('Data/patch-S.MPQ', 'report.json', 'CharSections.delta.dbc',
                         'turtle_forest_troll_skins.sql', 'rollback.sql', 'SHA256SUMS'):
                self.assertEqual((a / name).read_bytes(), (b / name).read_bytes(), name)
            self.assertEqual(first['counts']['final_rows'], 9048)
            self.assertEqual(first['preservation']['baseline_duplicate_tuples'], [])
            with self.assertRaises(ValueError):
                forest.build(a)


if __name__ == '__main__':
    unittest.main()
