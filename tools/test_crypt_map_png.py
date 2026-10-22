"""Reimport contracts using the exported real map; temporary outputs only."""
import json
from io import BytesIO
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from crypt_map_png import ROOT, import_png, palette_blp2, decode_map_blp


class PNGReimportTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory(dir='/tmp/opencode')
        self.root = Path(self.work.name)
        with Image.open(ROOT / 'work/karazhan-crypt-map-edit/original-en.png') as opened:
            self.image = opened.convert('RGBA')

    def tearDown(self):
        self.work.cleanup()

    def test_single_opaque_pixel_changes_only_its_dxt_block(self):
        self.assertEqual(self.image.getpixel((400, 45))[3], 255)
        self.image.putpixel((400, 45), (255, 0, 255, 255))
        path = self.root / 'edited.png'
        self.image.save(path)
        import_png(path, self.root / 'result')
        report = json.loads((self.root / 'result/report.json').read_text())
        self.assertEqual(len(report['changed_tiles']), 1)
        self.assertEqual(report['changed_tiles'][0]['tile'],
                         'Interface\\WorldMap\\KarazhanCrypt\\KarazhanCrypt2.blp')
        self.assertEqual(report['changed_tiles'][0]['blocks'], 1)

    def test_reject_resized_canvas(self):
        path = self.root / 'bad.png'
        self.image.resize((1002, 668)).save(path)
        with self.assertRaisesRegex(ValueError, '1024x768'):
            import_png(path, self.root / 'result')

    def test_palette_preserves_flat_letter_edges_and_transparency(self):
        image = Image.new('RGBA', (256, 256), (90, 70, 20, 255))
        image.putpixel((10, 11), (217, 91, 37, 255))
        image.putpixel((12, 14), (0, 0, 0, 0))
        with Image.open(BytesIO(palette_blp2(image))) as decoded:
            self.assertEqual(decoded.convert('RGBA').tobytes(), image.tobytes())
        encoded = bytearray(palette_blp2(image))
        for i in range(256):
            encoded[148+i*4+3] = 0  # BGRX padding must not supply pixel alpha.
        self.assertEqual(decode_map_blp(bytes(encoded)).tobytes(), image.tobytes())

    def test_reject_removed_transparency(self):
        path = self.root / 'bad.png'
        self.image.putalpha(255)
        self.image.save(path)
        with self.assertRaisesRegex(ValueError, 'Alpha/transparency changed'):
            import_png(path, self.root / 'result')


if __name__ == '__main__':
    unittest.main()
