#!/usr/bin/env python3
"""Contract tests for cartography merges and input validation (no MPQs needed)."""
import struct
import unittest

from build_crypt_cartography import (append_worldmap_area, blp_dimensions, group_header,
                                     hybrid_reasons, match_groups, merge_trs, parse_trs)
from dbc_write import read_dbc_bytes, write_dbc_bytes


def blp(width=64, height=32):
    size = ((width + 3) // 4) * ((height + 3) // 4) * 8
    return (b'BLP2' + struct.pack('<I4B2I', 1, 2, 1, 0, 0, width, height) +
            struct.pack('<16I', 148, *([0]*15)) +
            struct.pack('<16I', size, *([0]*15)) + bytes(size))


class TrsTests(unittest.TestCase):
    def test_preserves_full_baseline_and_original_crypt(self):
        base = (b'dir: WMO\\Dungeon\\MD_Crypt\r\n'
                b'WMO\\Dungeon\\MD_Crypt\\MD_Crypt_D_000_00_00.blp\tnative.blp\r\n'
                b'Other\\map00_00.blp\tother.blp')
        merged = merge_trs(base, [(r'WMO\Custom\Turtle800\tw800crypt_000_00_00.blp',
                                  'native.blp')])
        self.assertTrue(merged.startswith(base))
        self.assertEqual(len(parse_trs(merged)), 3)
        for key, value in parse_trs(base).items():
            self.assertEqual(parse_trs(merged)[key], value)

    def test_rejects_case_slash_collision_even_equal(self):
        for value in ('a.blp', 'different.blp'):
            with self.assertRaisesRegex(ValueError, 'collision'):
                merge_trs(b'A\\B.blp\ta.blp\n', [('a/b.BLP', value)])

    def test_rejects_duplicate_additions(self):
        with self.assertRaisesRegex(ValueError, 'collision'):
            merge_trs(b'', [('A\\B.blp', 'a.blp'), ('a/b.blp', 'b.blp')])

    def test_rejects_duplicate_baseline(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            parse_trs(b'A\\B.blp\ta.blp\na/b.BLP\ta.blp\n')

    def test_rejects_invalid_mapping(self):
        for data in (b'bad', b'A.blp ../escape.blp', b'../A.blp a.blp',
                     b'A.blp a.blp extra', b'A.blp a.blp\x00'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                parse_trs(data)

    def test_real_source_paths_with_spaces_and_subdirectory_values(self):
        parsed = parse_trs(b'WMO\\Collidable Doodads\\x.blp\tHighElfPVP\\map30_31.blp\n')
        self.assertEqual(len(parsed), 1)


class BlpTests(unittest.TestCase):
    def test_non_square_dxt1(self):
        self.assertEqual(blp_dimensions(blp()), [64, 32])

    def test_invalid_header_dimensions_and_ranges(self):
        cases = [b'', b'BLP1' + blp()[4:], blp()[:147], blp()[:-1]]
        for offset, value in ((4, 2), (12, 0), (12, 63), (16, 8192),
                              (20, 100), (20, 0xffffffff), (84, 1)):
            data = bytearray(blp())
            struct.pack_into('<I', data, offset, value)
            cases.append(bytes(data))
        for data in cases:
            with self.subTest(header=data[:24]), self.assertRaises(ValueError):
                blp_dimensions(data)


class DbcTests(unittest.TestCase):
    def setUp(self):
        self.rows = [[1, 0, 1519, 1, 0, 0, 0, 0, 0xffffffff, 0, 0],
                     [1043, 1, 0, 8, 0, 0, 0, 0, 0xffffffff, 0, 0]]
        self.strings = b'\0Unused\0Existing\0\xff\0'
        floats = list(struct.unpack('<4I', struct.pack('<4f', -1302.51, -1849.26, -10916.17, -11308.14)))
        self.source = write_dbc_bytes(8, [[674, 800, 5086, 1, *floats]], b'\0KarazhanCrypt\0')

    def test_preserves_records_and_unused_string_bytes(self):
        base = write_dbc_bytes(11, self.rows, self.strings)
        merged, report = append_worldmap_area(base, self.source)
        _, rows, strings = read_dbc_bytes(merged)
        self.assertEqual(rows[:-1], self.rows)
        self.assertEqual(merged[20:108], base[20:108])
        self.assertEqual(strings, self.strings + b'KarazhanCrypt\0')
        self.assertEqual(rows[-1][8:], [0xffffffff, 0, 0])
        self.assertEqual(report['rows_after'], 3)

    def test_all_three_collision_dimensions(self):
        for column, value in ((0, 674), (1, 800), (2, 5086)):
            rows = [self.rows[0].copy()]
            rows[0][column] = value
            with self.subTest(column=column), self.assertRaisesRegex(ValueError, 'collision'):
                append_worldmap_area(write_dbc_bytes(11, rows, self.strings), self.source)

    def test_truncated_table(self):
        with self.assertRaisesRegex(ValueError, 'layout'):
            append_worldmap_area(write_dbc_bytes(11, self.rows, self.strings)[:-1], self.source)


class HybridTests(unittest.TestCase):
    def test_xy_only_tolerance_and_dimensions(self):
        target = dict(bbox=[0, 1, 2, 3, 4, 5])
        source = dict(bbox=[0, 1, 200, 3.00001, 4, 500])
        images = {('00', '00'): dict(dimensions=[64, 32])}
        self.assertEqual(hybrid_reasons(target, source, images, images), [])
        source['bbox'][3] = 3.1
        self.assertIn('MOGP XY', hybrid_reasons(target, source, images, images)[0])
        other = {('00', '00'): dict(dimensions=[64, 64])}
        self.assertIn('BLP dimensions differ', hybrid_reasons(target, target, images, other))
        self.assertIn('image count differs', hybrid_reasons(target, target, images, {}))
        self.assertEqual(hybrid_reasons(target, source, {}, {}), [])

    def test_group_identity_from_mogp_not_index(self):
        header = bytearray(68)
        struct.pack_into('<6f', header, 12, 0, 1, 2, 3, 4, 5)
        struct.pack_into('<I', header, 56, 18873)
        data = b'PGOM' + struct.pack('<I', len(header)) + header
        self.assertEqual(group_header(data), dict(groupid=18873, bbox=[0, 1, 2, 3, 4, 5]))

    def test_reindexes_permuted_source_groups_by_identity(self):
        targets = [dict(index=0, groupid=10), dict(index=1, groupid=11),
                   dict(index=2, groupid=12)]
        sources = [dict(index=0, groupid=12), dict(index=1, groupid=10),
                   dict(index=2, groupid=11)]
        joined = match_groups(targets, sources)
        self.assertEqual([(t['index'], s['index']) for t, s in joined], [(0, 1), (1, 2), (2, 0)])
        with self.assertRaisesRegex(ValueError, 'sets differ'):
            match_groups(targets, sources[:-1])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            match_groups(targets, sources + [sources[0]])


if __name__ == '__main__':
    unittest.main()
