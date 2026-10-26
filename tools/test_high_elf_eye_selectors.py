"""Fail-closed selector migration and independent binary delta regressions."""
import struct
import unittest

from high_elf_eye_selectors import fix_selectors
from test_new_races_assets import validate_eye_delta


class EyeSelectors(unittest.TestCase):
    def setUp(self):
        self.geometry = {(22, s): {1702} for s in (0, 1)}
        # Distinct old-race and Goblin controls, including arbitrary non-eye fields.
        self.rows = [[1+i % 21, i // 21, i % 21, i, 7, 8, 9, i] for i in range(233)]
        self.rows += [[22, s, f, 1, 2, 3, 0, 0] for s in (0, 1) for f in range(11)]
        self.rows += [[23, 0, f, 4, 5, 6, 0, 0] for f in range(15)]

    def encode(self):
        return struct.pack('<4s4I', b'WDBC', len(self.rows), 8, 32, 8) + b''.join(
            struct.pack('<8I', *r) for r in self.rows) + b'\0kept!\0\0'

    def test_exact_delta_all_other_fields_and_idempotence(self):
        before = self.encode()
        after = fix_selectors(before, self.geometry)
        validate_eye_delta(before, after)
        expected = {20+i*32+28 for i, r in enumerate(self.rows) if r[0] == 22}
        self.assertEqual({i for i, (a, b) in enumerate(zip(before, after)) if a != b}, expected)
        self.assertEqual(fix_selectors(after, self.geometry), after)

    def test_unknown_and_partial_selectors_rejected(self):
        for value in (1, 2, 3, 0xffffffff):
            with self.subTest(value=value):
                self.rows[233][7] = value
                with self.assertRaisesRegex(ValueError, 'partially migrated'):
                    fix_selectors(self.encode(), self.geometry)

    def test_count_coverage_duplicate_and_geometry_rejected(self):
        for mutate in (lambda: self.rows.pop(),
                       lambda: self.rows[233].__setitem__(2, 11),
                       lambda: self.rows.__setitem__(234, self.rows[233].copy()),
                       lambda: self.geometry.pop((22, 1))):
            self.setUp()
            mutate()
            with self.assertRaises(ValueError):
                fix_selectors(self.encode(), self.geometry)

    def test_bad_schema_and_boundaries(self):
        raw = self.encode()
        for bad in (b'', b'XXXX'+raw[4:], raw[:-1], raw+b'\0', raw[:8]+struct.pack('<I', 9)+raw[12:]):
            with self.subTest(size=len(bad)), self.assertRaises(ValueError):
                fix_selectors(bad, self.geometry)

    def test_independent_validator_rejects_other_field_string_and_row_changes(self):
        before = self.encode()
        after = fix_selectors(before, self.geometry)
        for offset in (20+4*4, 20+233*32+24, len(after)-2):
            bad = bytearray(after)
            bad[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                validate_eye_delta(before, bytes(bad))
        with self.assertRaises(ValueError):
            validate_eye_delta(before, before)


if __name__ == '__main__':
    unittest.main()
