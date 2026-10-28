"""Unit tests and eleven hash-pinned real WMO fixtures from the staging tree.

Generate the candidate once with --native to populate the targeted Snapshot BLP
cache. HIGH_ELF_INTERIOR_ASSETS and HIGH_ELF_INTERIOR_TEXTURE_CACHE override the
default fixture locations. Real fixture tests explicitly skip if unavailable.
"""
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import high_elf_interior_minimaps as m
from build_crypt_cartography import blp_dimensions
from build_new_races_assets import blp_rgba

ROOT = Path(__file__).resolve().parent.parent


def chunk(tag, data):
    return tag.encode()[::-1]+struct.pack('<I', len(data))+data


def fixture_group(tris):
    vertices = [v for tri, mat in tris for v in tri]
    return bytes(68)+chunk('MOVT', b''.join(struct.pack('<3f', *v) for v in vertices))+chunk(
        'MOVI', b''.join(struct.pack('<3H', i*3, i*3+1, i*3+2) for i in range(len(tris))))+chunk(
        'MOPY', b''.join(bytes((0, mat)) for tri, mat in tris))


class ProjectionTests(unittest.TestCase):
    def test_projection_dimensions_padding_and_orientation(self):
        bbox = (-4, -7, 0, 6, 11, 9)
        self.assertEqual(m.dimensions(bbox), (32, 64))
        self.assertEqual(m.project((-4, -7, 0), bbox, 64), (0, 64))
        self.assertEqual(m.project((6, 11, 0), bbox, 64), (20, 28))
        self.assertEqual(m.dimensions((0, 0, 0, 16, 16, 0)), (32, 32))
        self.assertEqual(m.dimensions((0, 0, 0, 200, 200, 0)), (256, 256))
        group = fixture_group([([(0, 0, 0), (2, 0, 0), (0, 2, 0)], 1)])
        w, h, rgba, counts = m.raster(group, (0, 0, 0, 2, 2, 0), {1: [255, 0, 0]})
        self.assertEqual((w, h), (32, 32))
        self.assertEqual(rgba[:28*w*4], bytes(28*w*4))
        self.assertEqual(rgba[(31*w)*4:(31*w)*4+4], bytes((255, 0, 0, 255)))
        self.assertEqual(counts, {1: 1})

    def test_depth_real_xy_and_material_and_normal_selection(self):
        # Sloping upper triangle crosses the lower plane in real XY.
        base = [(0, 0, 1), (4, 0, 1), (0, 4, 1)]
        top = [(0, 0, 0), (4, 0, 4), (0, 4, 0)]
        rejected = [(0, 0, 99), (4, 0, 99), (0, 4, 99)]
        group = fixture_group([(base, 1), (top, 2), (rejected, 3), (list(reversed(rejected)), 1)])
        w, h, rgba, counts = m.raster(group, (0, 0, 0, 4, 4, 99),
                                      {1: [255, 0, 0], 2: [0, 255, 0]})
        self.assertEqual(counts, {1: 1, 2: 1})
        self.assertEqual(rgba[(31*w)*4:(31*w)*4+4], bytes((255, 0, 0, 255)))
        self.assertEqual(rgba[(31*w+4)*4:(31*w+4)*4+4], bytes((0, 255, 0, 255)))

    def test_codec_binary_alpha_rgb_and_stability(self):
        rgba = b''.join(bytes((231, 164, 62, 0 if i%3 == 0 else 255)) for i in range(64))
        encoded = m.encode_dxt1(8, 8, rgba)
        self.assertEqual(encoded, m.encode_dxt1(8, 8, rgba))
        self.assertEqual(blp_dimensions(encoded), [8, 8])
        decoded = blp_rgba(encoded)
        self.assertEqual(decoded[3::4], rgba[3::4])
        for i in range(0, len(rgba), 4):
            if rgba[i+3]:
                self.assertLessEqual(max(abs(decoded[i+c]-rgba[i+c]) for c in range(3)), 4)
        transparent = m.encode_dxt1(4, 4, bytes(64))
        self.assertEqual(blp_rgba(transparent), bytes(64))
        with self.assertRaisesRegex(ValueError, 'binary alpha'):
            m.encode_dxt1(4, 4, bytes((1, 2, 3, 128))*16)

    def test_guards(self):
        with self.assertRaisesRegex(ValueError, 'ManifestHash'):
            m.pinned(b'drift', '0'*64, 'root')
        with self.assertRaisesRegex(ValueError, 'Missing resource'):
            m.pinned(None, '0'*64, 'texture')
        with self.assertRaisesRegex(ValueError, 'Truncated'):
            m.chunks(b'bad')


class RealFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = Path(os.environ.get('HIGH_ELF_INTERIOR_ASSETS',
                          ROOT/'work/high-elf-assets-wmo-dry-fixed'))
        cls.cache = Path(os.environ.get('HIGH_ELF_INTERIOR_TEXTURE_CACHE',
                         ROOT/'work/high-elf-interior-minimaps-inputs/335'))
        if not (cls.assets/'files').is_dir() or not cls.cache.is_dir():
            raise unittest.SkipTest('Real WMO/targeted Snapshot texture fixtures unavailable')
        cls.plan = json.loads(m.PLAN.read_text())
        def resolver(name):
            path = cls.cache/(m.sha(name.replace('/', '\\').lower().encode())+'.bin')
            return path.read_bytes() if path.is_file() else None
        cls.resolver = staticmethod(resolver)
        cls.mapping = m.build_minimaps(cls.assets, resolver)

    def test_eleven_real_fixtures(self):
        self.assertEqual(len(self.mapping), 11)
        for spec in self.plan['groups']:
            with self.subTest(family=spec['family']):
                key = 'ter\\Custom\\HighElfMap\\'+spec['file']+'_001_00_00.blp'
                blp, meta = self.mapping[key]
                self.assertEqual(meta['grid'], [0, 0])
                self.assertEqual(len(meta['physical_name']), 36)
                self.assertEqual(meta['physical_name'], m.sha(blp)[:32]+'.blp')
                self.assertEqual(meta['dimensions'], blp_dimensions(blp))
                self.assertEqual(meta['selected_triangles'], sum(n for i, n in spec['triangles']))
                self.assertNotIn('nethermicro', key.lower())
                rgba = blp_rgba(blp)
                self.assertEqual(sum(bool(a) for a in rgba[3::4]), meta['opaque_pixels'])
                path = self.assets/'files/Character/Custom/HighElfMap'/(spec['file']+'_001.wmo')
                group = m.chunks(path.read_bytes())['MOGP']
                colors = {item['index']: item['average_rgb'] for item in meta['materials']}
                w, h, source, counts = m.raster(group, meta['bbox'], colors)
                self.assertEqual(source[3::4], rgba[3::4])
                # DXT1 endpoints are lossy, particularly where materials meet.
                errors = [abs(source[i+c]-rgba[i+c]) for i in range(0, len(source), 4)
                          if source[i+3] for c in range(3)]
                self.assertLess(sum(errors)/len(errors), 5)
                self.assertEqual(blp, m.encode_dxt1(w, h, source))

    def test_real_missing_and_drifting_textures(self):
        with self.assertRaisesRegex(ValueError, 'Missing resource'):
            m.build_minimaps(self.assets, lambda n: None)
        with self.assertRaisesRegex(ValueError, 'ManifestHash'):
            m.build_minimaps(self.assets, lambda n: b'drift')

    def test_real_root_and_group_drift(self):
        original = Path.read_bytes
        for suffix in ('.wmo', '_001.wmo'):
            def read(path):
                data = original(path)
                return data+b'drift' if path.name.endswith(suffix) else data
            with self.subTest(suffix=suffix), patch.object(Path, 'read_bytes', read):
                with self.assertRaisesRegex(ValueError, 'ManifestHash'):
                    m.build_minimaps(self.assets, self.resolver)

    def test_staged_texture_precedence(self):
        # Scrying Tower's custom floor is resolved locally, never via Snapshot.
        requested = []
        def resolve(name):
            requested.append(name)
            return self.resolver(name)
        self.assertEqual(self.mapping, m.build_minimaps(self.assets, resolve))
        self.assertEqual(len(requested), 4)
        self.assertFalse(any('Character' in name for name in requested))

    def test_fresh_candidate_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'candidate'
            report = m.write_candidate(out, self.mapping)
            self.assertEqual(len(report['tiles']), 11)
            for data, meta in self.mapping.values():
                self.assertEqual((out/meta['physical_name']).read_bytes(), data)
            with self.assertRaisesRegex(ValueError, 'fresh'):
                m.write_candidate(out, self.mapping)


if __name__ == '__main__':
    unittest.main()
