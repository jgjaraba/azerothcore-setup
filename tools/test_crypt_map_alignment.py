"""Regression checks for cropped edits and interpolation boundaries."""
import unittest

import numpy as np

from align_crypt_map_png import align_pixels


class AlignmentCoverageTests(unittest.TestCase):
    def setUp(self):
        self.original = np.zeros((768, 1024, 4), dtype='uint8')
        self.original[:668, :1002] = (120, 70, 20, 255)
        self.edited = np.zeros_like(self.original)
        self.edited[:685] = (120, 70, 20, 255)

    def test_marginal_cropped_edge_preserves_original_not_black(self):
        matrix = np.array([[1.02321, 0, 0], [0, 1.02321, 0]], dtype='float64')
        result, report = align_pixels(self.original, self.edited, matrix)
        visible = self.original[:, :, 3] > 0
        self.assertGreater(report['restored_boundary_pixels'], 0)
        self.assertLessEqual(np.abs(result[visible].astype('int16')
                                    - self.original[visible]).max(), 1)
        self.assertTrue(np.array_equal(result[:3, :1002], self.original[:3, :1002]))
        self.assertTrue(np.array_equal(result[:, :, 3], self.original[:, :, 3]))

    def test_significant_cropped_zoom_rejected(self):
        matrix = np.array([[1.09, 0, 0], [0, 1.09, 0]], dtype='float64')
        with self.assertRaisesRegex(ValueError, 'clips significant'):
            align_pixels(self.original, self.edited, matrix)


if __name__ == '__main__':
    unittest.main()
