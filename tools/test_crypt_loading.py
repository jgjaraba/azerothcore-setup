"""Regression tests for byte-preserving client DBC and malformed BLP repair."""
import struct
import unittest

from build_crypt_loading import ART, append_loading, normalize_blp, table, update_map


def dbc(rows, strings=b'\0'):
    fields = len(rows[0])
    return (struct.pack('<4s4I', b'WDBC', len(rows), fields, fields*4, len(strings))
            + b''.join(struct.pack('<'+'I'*fields, *row) for row in rows) + strings)


def blp():
    raw = bytearray(1172)
    raw[:4] = b'BLP2'
    struct.pack_into('<I4B2I', raw, 4, 1, 2, 0, 0, 1, 512, 512)
    for level in range(10):
        size = ((max(1, 512 >> level)+3)//4)**2*8
        struct.pack_into('<I', raw, 20+4*level, len(raw))
        struct.pack_into('<I', raw, 84+4*level, size)
        raw.extend(bytes([level+17])*size)
    struct.pack_into('<I', raw, 60, len(raw))
    struct.pack_into('<I', raw, 124, 4294791348)
    struct.pack_into('<I', raw, 144, 131072)
    return bytes(raw)


class LoadingTests(unittest.TestCase):
    def test_tail_fix_preserves_every_active_compressed_byte(self):
        raw = blp()
        result, info = normalize_blp(raw)
        allowed = set(range(60, 84)) | set(range(124, 148))
        self.assertTrue(all(a == b for i, (a, b) in enumerate(zip(raw, result)) if i not in allowed))
        self.assertEqual(len(raw), len(result))
        self.assertEqual(result[60:84], bytes(24))
        self.assertEqual(result[124:148], bytes(24))
        for start, end in info['active_ranges']:
            self.assertEqual(result[start:end], raw[start:end])
        self.assertEqual(normalize_blp(result)[0], result)

    def test_rejects_bad_active_offset_size_overlap_and_truncation(self):
        for pos, value in ((20, 0), (20, 175948), (84, 8), (24, 1172)):
            with self.subTest(pos=pos, value=value):
                raw = bytearray(blp())
                struct.pack_into('<I', raw, pos, value)
                with self.assertRaises(ValueError):
                    normalize_blp(bytes(raw))
        with self.assertRaises(ValueError):
            normalize_blp(blp()[:-1])

    def test_loading_preserves_unsorted_native_records_and_unused_strings(self):
        ids = [254] + list(range(90))
        rows = [(i, 0, 0, i % 2) for i in ids]
        raw = dbc(rows, b'\0unreferenced native string\0')
        result, _ = append_loading(raw, 'Karazhan Crypt', ART)
        actual, strings = table(result, 4)
        self.assertEqual(actual[:-1], rows)
        self.assertEqual(result[20:20+91*16], raw[20:20+91*16])
        self.assertTrue(strings.startswith(b'\0unreferenced native string\0'))
        self.assertEqual(actual[-1][0], 511)
        self.assertEqual(actual[-1][3], 0)

    def test_maps_keep_their_own_strings_offsets_and_change_only_field57(self):
        rows = [[i]+[i*100+j for j in range(1, 66)] for i in range(136)]
        rows[42][0], rows[42][57] = 800, 0
        for block, offset in ((b'\0English\0', 1), (b'\0padding\0Spanish\0', 9)):
            rows[42][1] = offset
            raw = dbc(rows, block)
            result, _ = update_map(raw)
            start = 20+42*264+57*4
            self.assertEqual(result[:start], raw[:start])
            self.assertEqual(result[start+4:], raw[start+4:])
            self.assertEqual(struct.unpack_from('<I', result, start)[0], 511)
            self.assertEqual(table(result, 66)[1], block)
        rows[0][57] = 511
        with self.assertRaises(ValueError):
            update_map(dbc(rows))

    def test_dbc_rejects_duplicate_ids_and_truncated_strings(self):
        with self.assertRaises(ValueError):
            table(dbc([(1, 0, 0, 0), (1, 0, 0, 0)]), 4)
        with self.assertRaises(ValueError):
            table(dbc([(1, 0, 0, 0)])[:-1], 4)


if __name__ == '__main__':
    unittest.main()
