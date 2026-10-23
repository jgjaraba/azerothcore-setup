"""Synthetic A/B encoder tests; opt-in package test uses only published v2."""
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np

import build_troll_face_format_test as trial


class PaletteTests(unittest.TestCase):
    def test_top_pixels_and_alpha_are_lossless(self):
        rng = np.random.default_rng(197)
        for translucent in (False, True):
            rgba = np.empty((8, 16, 4), dtype=np.uint8)
            rgba[:, :, :3] = rng.integers(0, 256, (8, 16, 3), dtype=np.uint8)
            rgba[:, :, 3] = rng.integers(0, 256, (8, 16), dtype=np.uint8) if translucent else 255
            source = trial.troll.encode_blp(rgba)
            raw, report = trial.palette_encode(source)
            self.assertEqual(raw[8], 1)
            self.assertEqual(raw[9], 8 if translucent else 0)
            self.assertEqual(raw[10], 8)
            np.testing.assert_array_equal(trial.troll.decode_blp(raw), rgba)
            self.assertEqual(report['mip_errors'][0]['rgb_max'], 0)
            self.assertTrue(report['all_mip_alpha_exact'])
            self.assertEqual(trial.palette_encode(source)[0], raw)

    def test_too_many_top_colours_refused_without_quantization(self):
        rgba = np.zeros((32, 32, 4), dtype=np.uint8)
        rgba[:, :, 0] = np.arange(32, dtype=np.uint8)[:, None]
        rgba[:, :, 1] = np.arange(32, dtype=np.uint8)[None]
        rgba[:, :, 3] = 255
        with self.assertRaisesRegex(ValueError, 'losslessly'):
            trial.palette_encode(trial.troll.encode_blp(rgba))

    def test_wrong_input_format_refused(self):
        rgba = np.full((4, 4, 4), 255, dtype=np.uint8)
        palette, _ = trial.palette_encode(trial.troll.encode_blp(rgba))
        with self.assertRaisesRegex(ValueError, 'BGRA'):
            trial.palette_encode(palette)

    def test_normal_publication_cannot_be_an_output(self):
        with self.assertRaises(ValueError):
            trial.build(trial.BASE)
        with self.assertRaisesRegex(ValueError, 'Choose'):
            trial.build(Path('/tmp/not-a-client-output'))


@unittest.skipUnless(os.environ.get('TROLL_FACE_AB_INTEGRATION') == '1', 'opt-in published patch fixture')
class PublishedPatchTests(unittest.TestCase):
    def test_two_candidates_same_hash_and_only_two_changed_members(self):
        with tempfile.TemporaryDirectory(prefix='troll-face-tests-', dir=trial.ROOT / 'work') as temp:
            first = trial.build(Path(temp) / 'first')
            second = trial.build(Path(temp) / 'second')
            self.assertEqual(first, second)
            self.assertEqual(first['checks']['changed_members'], 2)
            self.assertEqual(first['selected']['skin'], 24)
            for change in first['changes']:
                self.assertTrue(change['top_rgba_exact'])
                self.assertTrue(change['all_mip_alpha_exact'])


if __name__ == '__main__':
    unittest.main()
