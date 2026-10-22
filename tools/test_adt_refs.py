"""Regression tests for variable-length ADT model-name replacements."""
import struct
import unittest

from adt_refs import name_offsets, remap_name_table


class ModelOffsetTests(unittest.TestCase):
    def test_shortened_extensions_keep_reordered_and_repeated_slots(self):
        old = b'first.mdx\0second.mdx\0third.mdx\0'
        new = b'first.m2\0second.m2\0third.m2\0'
        # MMID is an indirection table, not necessarily string-table order.
        slots = struct.pack('<4I', 21, 0, 10, 21)
        repaired = remap_name_table(old, new, slots)
        self.assertEqual(struct.unpack('<4I', repaired), (19, 0, 9, 19))
        self.assertEqual([name_offsets(new)[o] for (o,) in struct.iter_unpack('<I', repaired)],
                         [b'third.m2', b'first.m2', b'second.m2', b'third.m2'])

    def test_offset_into_string_rejected(self):
        with self.assertRaises(ValueError):
            remap_name_table(b'first.mdx\0', b'first.m2\0', struct.pack('<I', 1))

    def test_unterminated_name_rejected(self):
        with self.assertRaises(ValueError):
            name_offsets(b'first.mdx')

    def test_shape_change_rejected(self):
        with self.assertRaises(ValueError):
            remap_name_table(b'a\0b\0', b'a\0', struct.pack('<I', 0))

    def test_truncated_index_rejected(self):
        with self.assertRaises(ValueError):
            remap_name_table(b'a\0', b'a\0', b'\0\0')


if __name__ == '__main__':
    unittest.main()
