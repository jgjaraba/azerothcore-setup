"""Synthetic parser tests; no client assets or running server required."""
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

import audit_turtle_skins as audit


class SkinAuditTests(unittest.TestCase):
    def test_charsections_layouts_are_not_interchangeable(self):
        names = {0: '', 20: 'body.blp', 30: 'extra.blp'}
        turtle = [123, 8, 1, 0, 2, 6, 20, 30, 0, 1]
        wrath = [123, 8, 1, 0, 20, 30, 0, 1, 2, 6]
        decoded = audit.section('turtle', turtle, names.__getitem__)
        self.assertEqual(decoded, audit.section('335', wrath, names.__getitem__))
        self.assertEqual(decoded['textures'], ['body.blp', 'extra.blp', ''])
        self.assertEqual(decoded['color'], 6)
        # This decoder deliberately does not convert Vanilla eligibility flags.
        self.assertEqual(decoded['flags'], 1)
        with self.assertRaises(ValueError):
            audit.section('unknown', wrath, names.__getitem__)

    def test_blp_dimensions_include_blp2_type_field(self):
        for magic in (b'BLP1', b'BLP2'):
            raw = magic + bytes(8) + struct.pack('<II', 512, 256)
            self.assertEqual(audit.texture_dimensions(raw), (512, 256))
        with self.assertRaises(ValueError):
            audit.texture_dimensions(b'not-a-blp')

    def test_dbc_strings_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test.dbc'
            path.write_bytes(struct.pack('<4s4I', b'WDBC', 1, 2, 8, 5)
                             + struct.pack('<II', 7, 1) + b'\0abc\0')
            meta, rows, text = audit.dbc(path)
            self.assertEqual(meta['fields'], 2)
            self.assertEqual(rows, [[7, 1]])
            self.assertEqual(text(1), 'abc')
            with self.assertRaises(ValueError):
                text(5)
            path.write_bytes(path.read_bytes()[:-1] + b'x')
            _, _, text = audit.dbc(path)
            with self.assertRaises(ValueError):
                text(1)

    def test_existing_output_rejected_before_client_access(self):
        (audit.ROOT / 'work').mkdir(exist_ok=True)
        result = subprocess.run([sys.executable, audit.__file__, '--output',
                                 str(audit.ROOT / 'work')], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('new subdirectory', result.stderr)
        with tempfile.TemporaryDirectory(prefix='skin-audit-test-', dir=audit.ROOT / 'work') as tmp:
            result = subprocess.run([sys.executable, audit.__file__, '--output', tmp],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('already exists', result.stderr)


if __name__ == '__main__':
    unittest.main()
