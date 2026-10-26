"""Imaging-dependent codec checks; run with the pinned image environment."""
import struct
import unittest
from PIL import Image
from build_new_races_assets import blp_rgba, palette_rgba
from new_races_palette import normalize


class PaletteNormalization(unittest.TestCase):
    def test_independent_dxt1_mips_and_binary_alpha(self):
        # DXT1 reference pixels explicitly specified independently of our decoder.
        for transparent in (False, True):
            a, b = (0x001f, 0xf800) if transparent else (0xf800, 0x001f)
            colors = ([(0, 0, 255, 255), (255, 0, 0, 255), (127, 0, 127, 255), (0, 0, 0, 0)]
                      if transparent else [(255, 0, 0, 255), (0, 0, 255, 255),
                                           (170, 0, 85, 255), (85, 0, 170, 255)])
            block = struct.pack('<HHI', a, b, sum((i % 4) << (2*i) for i in range(16)))
            dims = [(4, 4), (2, 2), (1, 1)]
            raw = struct.pack('<4sI4B2I', b'BLP2', 1, 2, int(transparent), 0, 1, 4, 4)
            raw += struct.pack('<16I', 1172, 1180, 1188, *([0]*13))
            raw += struct.pack('<16I', 8, 8, 8, *([0]*13))+bytes(1024)+block*3
            expected = []
            for level, (w, h) in enumerate(dims):
                rgba = b''.join(bytes(colors[x]) for y in range(h) for x in range(w))
                expected.append(rgba)
                self.assertEqual(blp_rgba(raw, level), rgba)
            # Independent library verifies the source DXT1 graphics/top alpha.
            # Pillow's BLP plugin truncates 565 endpoints; use its independent
            # native BCn decoder, which expands endpoints like the client.
            self.assertEqual(Image.frombytes('RGBA', (4, 4), block, 'bcn', 1).tobytes(), expected[0])
            encoded, proof = normalize(raw)
            self.assertEqual(encoded[8], 1)
            self.assertEqual(struct.unpack_from('<I', encoded, 20)[0], 1172)
            for level in range(3):
                self.assertEqual(palette_rgba(encoded, level), expected[level])
            self.assertEqual(len(proof['mips']), 3)
            self.assertEqual(normalize(raw)[0], encoded)


if __name__ == '__main__':
    unittest.main()
