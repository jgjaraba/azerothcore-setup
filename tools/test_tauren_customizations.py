#!/usr/bin/env python3
"""Tauren contracts, independent binary checks and isolated SQL regression tests.

Run with the pinned customization Python. TAUREN_INTEGRATION=1 rebuilds twice
from pinned read-only clients and accepted Troll publications, then runs private
MySQL tests too. TAUREN_FIXTURE=/absolute/work/build permits artifact/SQL checks
without rebuilding (for example work/tauren-build-r3); it never publishes.
No connection to the DEV database is made. All SQL uses self-contained DDL.
"""
import json
import os
from pathlib import Path
import pwd
import struct
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np

import build_tauren_customizations as builder
import tauren_geosets as geosets
import test_forest_troll_sql as mysql_fixture

ROOT = Path(__file__).resolve().parents[1]
CODEC = builder.codec
FOREST = CODEC.forest
INTEGRATION = os.environ.get('TAUREN_INTEGRATION') == '1'
FIXTURE = os.environ.get('TAUREN_FIXTURE')
NATURAL = [(6, 0, 7, 10, 10, 10, 0, 0), (6, 0, 8, 11, 11, 11, 0, 0),
           (6, 1, 5, 0, 0, 6, 0, 0), (6, 1, 6, 0, 0, 7, 0, 0)]


def records(raw, header, width):
    """Independent bounds-checked reader; do not use the converter's reader."""
    count, offset = struct.unpack_from('<II', raw, header)
    if count and (offset < 4 or offset + count * width > len(raw)):
        raise AssertionError('Binary array outside file')
    return [raw[offset+i*width:offset+(i+1)*width] for i in range(count)]


def u16(rows):
    return [struct.unpack('<H', row)[0] for row in rows]


def put(raw, header, rows):
    """Minimal synthetic fixture serializer, deliberately without alignment."""
    struct.pack_into('<II', raw, header, len(rows), len(raw))
    raw.extend(b''.join(rows))


def vertex(index):
    return (struct.pack('<3f', index / 10, 0., 0.) + bytes((192, 63, 0, 0))
            + bytes((1, 0, 255, 255)) + struct.pack('<3f2f2I', 0., 0., 1., 0., 0., 0, 0))


def synthetic_models(sex=0):
    source, native = bytearray(400), bytearray(320)
    source[:8] = b'MD20' + struct.pack('<I', 256)
    native[:8] = b'MD20' + struct.pack('<I', 264)
    struct.pack_into('<6f', native, 160, -10., -10., -10., 10., 10., 10.)
    sb, nb = [], []
    for i, parent in enumerate((-1, 0)):
        head = struct.pack('<iIhH', i, 0, parent, 0)
        pivot = struct.pack('<3f', i / 2, 0., 0.)
        sb.append(head + bytes(84) + pivot)
        nb.append(head + bytes(64) + pivot)
    put(source, 52, sb); put(native, 44, nb)
    ids = [110, 111] if sex == 0 else [206, 207, 207]
    verts = [vertex(i) for i in range(3 * len(ids))]
    put(source, 68, verts); put(native, 60, [vertex(0)])
    struct.pack_into('<I', native, 68, 3)
    view = len(source)
    source.extend(bytes(44))
    struct.pack_into('<II', source, 76, 1, view)
    shorts = [struct.pack('<H', i) for i in range(len(verts))]
    put(source, view, shorts); put(source, view + 8, shorts)
    sections, batches = [], []
    for i, identity in enumerate(ids):
        sections.append(struct.pack('<10H3f', identity, 0, i*3, 3, i*3, 3, 2, 0, 2, 0, 0., 0., 0.))
        batch = bytearray(24)
        struct.pack_into('<H', batch, 4, i)
        batches.append(bytes(batch))
    put(source, view+24, sections); put(source, view+32, batches)
    put(source, 92, [struct.pack('<4I', 8, 0, 0, 0)])
    put(native, 80, [struct.pack('<4I', 8, 0, 0, 0)])
    put(source, 148, [bytes(2)]); put(native, 128, [bytes(2)])
    put(source, 132, [struct.pack('<2H', 4, 1)])
    put(native, 112, [bytes(4)])
    put(native, 120, [bytes(2)])
    skin = bytearray(b'SKIN' + bytes(44))
    struct.pack_into('<I', skin, 44, 4)
    put(skin, 4, [bytes(2)]); put(skin, 12, [bytes(2)] * 3)
    put(skin, 20, [bytes(4)]); put(skin, 28, [bytes(48)])
    template = bytearray(24)
    struct.pack_into('<H', template, 14, 1)
    put(skin, 36, [bytes(template)])
    return bytes(source), bytes(native), [bytes(skin)] * 3


def check_geometry(test, source, native, oldskins, result, skins, sex):
    """Verify the emitted geometry from source topology, not converter metadata."""
    allowed = set(range(60, 68)) | set(range(112, 128))
    test.assertGreater(len(result), len(native))
    test.assertEqual(bytes(v for i, v in enumerate(result[:len(native)]) if i not in allowed),
                     bytes(v for i, v in enumerate(native) if i not in allowed))
    nv, rv = records(native, 60, 48), records(result, 60, 48)
    test.assertEqual(rv[:len(nv)], nv)
    for header, width in ((112, 4), (120, 2)):
        old = records(native, header, width)
        test.assertEqual(records(result, header, width)[:len(old)], old)
    sv = records(source, 68, 48)
    view = struct.unpack_from('<I', source, 80)[0]
    lookup, triangles = u16(records(source, view, 2)), u16(records(source, view+8, 2))
    all_source_sections = records(source, view+24, 32)
    wanted = {110, 111} if sex == 0 else {206, 207}
    added = [(i, struct.unpack('<10H3f', row)) for i, row in enumerate(all_source_sections)
             if struct.unpack_from('<H', row)[0] in wanted]
    test.assertEqual(len(added), 2 if sex == 0 else 3)
    test.assertEqual({r[0] for _, r in added}, wanted)
    test.assertEqual(len(rv), len(nv) + sum(r[3] for _, r in added))
    global_start = len(nv)
    sb, nb = records(source, 52, 108), records(native, 44, 88)
    source_batches = records(source, view+32, 24)
    flags = records(result, 112, 4)
    bones = u16(records(result, 120, 2))
    test.assertEqual(len(skins), len(oldskins))
    for old, new in zip(oldskins, skins):
        test.assertEqual(new[:4], b'SKIN')
        test.assertEqual(new[44:len(old)], old[44:])
        arrays = {}
        for header, width in ((4, 2), (12, 2), (20, 4), (28, 48), (36, 24)):
            before, after = records(old, header, width), records(new, header, width)
            test.assertEqual(after[:len(before)], before)
            arrays[header] = (before, after)
        test.assertEqual(len(arrays[28][1]), len(arrays[28][0]) + len(added))
        test.assertEqual(len(arrays[36][1]), len(arrays[36][0]) + len(added))
        g = global_start
        for offset, (si, section) in enumerate(added):
            identity, _, start, count, first, nindices = section[:6]
            vertices = [sv[i] for i in lookup[start:start+count]]
            test.assertEqual(rv[g:g+count], vertices)
            subindex = len(arrays[28][0]) + offset
            sub = struct.unpack('<10H7f', arrays[28][1][subindex])
            test.assertEqual(sub[:2], (identity, 0))
            vs, vc, ts, tc, bonecount, combo, influences = sub[2:9]
            test.assertEqual((vc, tc), (count, nindices))
            test.assertEqual(vs, len(arrays[4][0]) + sum(r[3] for _, r in added[:offset]))
            test.assertEqual(ts, len(arrays[12][0]) + sum(r[5] for _, r in added[:offset]))
            test.assertEqual(u16(arrays[4][1][vs:vs+vc]), list(range(g, g+vc)))
            expected_triangles = [vs + i - start for i in triangles[first:first+nindices]]
            actual_triangles = u16(arrays[12][1][ts:ts+tc])
            test.assertEqual(actual_triangles, expected_triangles)
            test.assertEqual(tc % 3, 0)
            test.assertTrue(all(vs <= i < vs+vc for i in actual_triangles))
            used = sorted({b for v in vertices for w, b in zip(v[12:16], v[16:20]) if w})
            test.assertEqual(bones[combo:combo+bonecount], used)
            test.assertEqual(influences, max(sum(w > 0 for w in v[12:16]) for v in vertices))
            for v, prop in zip(vertices, arrays[20][1][vs:vs+vc]):
                for weight, bone, local in zip(v[12:16], v[16:20], prop):
                    if weight:
                        test.assertLess(local, bonecount)
                        test.assertEqual(bones[combo+local], bone)
                        # Check only used bones and ancestors, never unused116.
                        seen = set()
                        while bone >= 0:
                            test.assertNotIn(bone, seen); seen.add(bone)
                            test.assertEqual(sb[bone][:12], nb[bone][:12])
                            test.assertEqual(sb[bone][-12:], nb[bone][-12:])
                            bone = struct.unpack_from('<h', sb[bone], 8)[0]
            batch = arrays[36][1][len(arrays[36][0])+offset]
            test.assertEqual(struct.unpack_from('<2H', batch, 4), (subindex, subindex))
            original = [b for b in source_batches if struct.unpack_from('<H', b, 4)[0] == si]
            test.assertEqual(len(original), 1)
            material = struct.unpack_from('<H', original[0], 10)[0]
            test.assertEqual(flags[struct.unpack_from('<H', batch, 10)[0]], records(source, 132, 4)[material])
            test.assertEqual(struct.unpack_from('<H', batch, 14)[0], 1)
            texture = u16(records(result, 128, 2))[struct.unpack_from('<H', batch, 16)[0]]
            test.assertEqual(struct.unpack_from('<I', records(result, 80, 16)[texture])[0], 8)
            templates = [b for b in arrays[36][0] if struct.unpack_from('<H', b, 14)[0] == 1
                         and struct.unpack_from('<I', records(native, 80, 16)[
                             u16(records(native, 128, 2))[struct.unpack_from('<H', b, 16)[0]]])[0] == 8]
            test.assertTrue(templates)
            expected_batch = bytearray(templates[0])
            struct.pack_into('<2H', expected_batch, 4, subindex, subindex)
            struct.pack_into('<H', expected_batch, 10, struct.unpack_from('<H', batch, 10)[0])
            test.assertEqual(batch, bytes(expected_batch))
            positions = np.array([struct.unpack_from('<3f', v) for v in vertices])
            np.testing.assert_allclose(sub[10:13], positions.mean(0), atol=1e-5)
            box = (positions.min(0)+positions.max(0))/2
            np.testing.assert_allclose(sub[13:16], box, atol=1e-5)
            test.assertAlmostEqual(sub[16], np.linalg.norm(positions-box, axis=1).max(), places=4)
            g += vc
        for header, per_vertex in ((4, True), (12, False), (20, True)):
            test.assertEqual(len(arrays[header][1]), len(arrays[header][0]) +
                             sum(r[3 if per_vertex else 5] for _, r in added))


class SyntheticTests(unittest.TestCase):
    def test_both_sexes_append_preserve_and_remap_all_lods(self):
        for sex in (0, 1):
            with self.subTest(sex=sex):
                source, native, skins = synthetic_models(sex)
                result, output, _ = geosets.convert(source, native, skins, sex)
                check_geometry(self, source, native, skins, result, output, sex)

    def test_used_bone_parent_mismatch_refused(self):
        source, native, skins = synthetic_models()
        bad = bytearray(source)
        offset = struct.unpack_from('<I', source, 56)[0]
        bad[offset+108-12] ^= 1  # root pivot: ancestor of weighted bone1
        with self.assertRaisesRegex(ValueError, 'Bind skeleton mismatch'):
            geosets.convert(bytes(bad), native, skins, 0)

    def test_triangle_outside_own_section_refused(self):
        source, native, skins = synthetic_models()
        bad = bytearray(source)
        view = struct.unpack_from('<I', source, 80)[0]
        offset = struct.unpack_from('<I', source, view+12)[0]
        struct.pack_into('<H', bad, offset, 3)
        with self.assertRaisesRegex(ValueError, 'Triangle outside section'):
            geosets.convert(bytes(bad), native, skins, 0)

    def test_extra_texture_type_and_lod_capacity_refused(self):
        source, native, skins = synthetic_models()
        bad = bytearray(source)
        struct.pack_into('<I', bad, struct.unpack_from('<I', source, 96)[0], 6)
        with self.assertRaisesRegex(ValueError, 'extra-skin texture'):
            geosets.convert(bytes(bad), native, skins, 0)
        skin = bytearray(skins[0]); struct.pack_into('<I', skin, 44, 1)
        with self.assertRaisesRegex(ValueError, 'bone palette capacity'):
            geosets.convert(source, native, [bytes(skin)]*3, 0)

    def test_generated_palette_encoding_and_independent_alpha_mips(self):
        rgba = np.random.default_rng(616).integers(0, 256, (16, 32, 4), dtype=np.uint8)
        bgra = CODEC.encode_blp(rgba)
        raw, _ = builder.palette_encode(bgra, allow_quantize=True)
        self.assertEqual((raw[8], raw[9], raw[10]), (1, 8, 8))
        info = FOREST.validate_blp(raw)
        for level, mip in enumerate(info['mips']):
            count = mip['width'] * mip['height']
            alpha = np.frombuffer(raw, np.uint8, count, mip['offset']+count)
            original = CODEC.decode_blp(bgra, level)[:, :, 3].reshape(-1)
            np.testing.assert_array_equal(alpha, original)

    def test_sql_namespaces_guards_and_transactions(self):
        row = [21000, 6, 0, 0, 'Character\\Custom\\TurtleTauren\\test.blp', '', '', 17, 0, 25]
        for optional in (False, True):
            for rollback in (False, True):
                text = builder.sql([row], optional, rollback, prerequisites=[row] if optional and not rollback else (),
                                   dependents=[row] if rollback and not optional else ())
                self.assertIn('tauren_extra_skins' if optional else 'tauren_primary', text)
                self.assertIn('ROLLBACK; RESIGNAL', text)
                for column in ('TexturePath1', 'TexturePath2', 'TexturePath3'):
                    self.assertIn(f'CAST(a.`{column}` AS BINARY)', text)
                self.assertNotIn('UPDATE ', text)
                if optional and not rollback:
                    self.assertIn('Optional Tauren requires exact principal prerequisites', text)
                if rollback and not optional:
                    self.assertIn('Remove optional skins before primary rollback', text)


@unittest.skipUnless(INTEGRATION or FIXTURE, 'TAUREN_INTEGRATION=1 or TAUREN_FIXTURE opt-in')
class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(builder.RECIPE.read_text())
        cls.protected = {ROOT / spec['path'] / name: value
                         for spec in cls.recipe['bases'].values() for name, value in spec['files'].items()}
        cls.archives = {}
        for label, spec in cls.recipe['archives'].items():
            path = Path('/home/dev/wow-' + ('335' if spec['client'] == '335' else 'turtle')) / spec['path']
            cls.archives[label] = path
            cls.protected[path] = spec['sha256']
        for path, expected in cls.protected.items():
            if CODEC.sha(path) != expected:
                raise AssertionError('Pinned input changed: ' + str(path))
        cls.temp = tempfile.TemporaryDirectory(prefix='tauren-tests-', dir=ROOT / 'work')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.addClassCleanup(cls.check_protected)
        cls.base = Path(cls.temp.name)
        cls.first = Path(FIXTURE).resolve() if FIXTURE and not INTEGRATION else cls.base / 'first'
        if INTEGRATION:
            builder.build(cls.first)
            time.sleep(1.1)
            cls.second = cls.base / 'second'
            builder.build(cls.second)
        cls.reports, cls.payload, cls.old = {}, {}, {}
        for edition, spec in cls.recipe['bases'].items():
            cls.reports[edition] = json.loads((cls.first / edition / 'report.json').read_text())
            cls.payload[edition] = dict(builder.members(FOREST.MPQ, cls.first / edition / 'Data/patch-S.MPQ').values())
            cls.old[edition] = dict(builder.members(FOREST.MPQ, ROOT / spec['path'] / 'Data/patch-S.MPQ').values())
        cls.source_cache = {}

    @classmethod
    def check_protected(cls):
        for path, expected in cls.protected.items():
            if CODEC.sha(path) != expected:
                raise AssertionError('Read-only input mutated: ' + str(path))

    @classmethod
    def source(cls, client, name):
        label = client + ':' + (name if name.startswith('table:') else name.lower())
        if label not in cls.source_cache:
            spec = cls.recipe['assets'][label]
            raw = FOREST.extract(cls.archives[spec['archive']], spec['member'], cls.base / 'extract')
            if CODEC.digest(raw) != spec['sha256']:
                raise AssertionError('Source member hash mismatch ' + label)
            cls.source_cache[label] = raw
        return cls.source_cache[label]

    @unittest.skipUnless(INTEGRATION, 'Two source builds require TAUREN_INTEGRATION=1')
    def test_two_source_builds_all_products_identical(self):
        first = {p.relative_to(self.first): p.read_bytes() for p in self.first.rglob('*') if p.is_file()}
        second = {p.relative_to(self.second): p.read_bytes() for p in self.second.rglob('*') if p.is_file()}
        self.assertEqual(first.keys(), second.keys())
        for name in first:
            self.assertEqual(first[name], second[name], str(name))

    def test_all_old_rows_resources_and_only30_native_flag_changes(self):
        for edition in self.payload:
            with self.subTest(edition=edition):
                old, new = self.old[edition], self.payload[edition]
                for name, raw in old.items():
                    if name not in (builder.SECTION, builder.STYLES):
                        self.assertEqual(new[name], raw, name)
                before, strings = FOREST.read_dbc(old[builder.SECTION])
                after, newstrings = FOREST.read_dbc(new[builder.SECTION])
                self.assertTrue(newstrings.startswith(strings))
                self.assertEqual(len(after), 9302 if edition == 'primary' else 9452)
                byid = {r[0]: r for r in after}
                self.assertEqual(len(byid), len(after))
                changes = []
                for row in before:
                    actual = byid[row[0]]
                    if actual != row:
                        changes.append(row[0])
                        self.assertEqual(row[:7] + row[8:], actual[:7] + actual[8:])
                        self.assertEqual((row[1], row[3], row[7], actual[7]), (6, 3, 0x12, 0x13))
                self.assertEqual(len(changes), 30)
                report = self.reports[edition]
                fresh = report['primary_rows'] + (report['optional_rows'] if edition == 'optional' else [])
                expected = {r[0]: tuple(r) for r in fresh}
                self.assertEqual(set(byid)-{r[0] for r in before}, {i for i in expected if i >= 21000})
                for identity, decoded in expected.items():
                    self.assertEqual(FOREST.decode(byid[identity], newstrings), decoded)

    def test_primary_facebank_body_correspondence_hair_and_allocations(self):
        report = self.reports['primary']
        rows = report['primary_rows']
        self.assertEqual(len(rows), 193)
        self.assertEqual(sorted(r[0] for r in rows if r[0] >= 21000), list(range(21000, 21163)))
        self.assertEqual(len([r for r in rows if r[0] < 21000]), 30)
        source, block = FOREST.read_dbc(self.source('turtle', 'table:CharSections'))
        source = [FOREST.decode(r, block, 'turtle') for r in source]
        payload = self.payload['primary']
        for sex, sc, tc, nfaces, styles in ((0, 19, 25, 5, 13), (1, 11, 17, 4, 12)):
            selected = [r for r in rows if r[2] == sex and r[3] in (0, 1, 4)]
            original = [r for r in source if r[1:3] == (6, sex) and r[3] in (0, 1, 4) and r[7] == 0 and r[9] == sc]
            self.assertEqual(len(selected), nfaces+2)
            self.assertEqual({r[9] for r in selected}, {tc})
            faces = [r for r in selected if r[3] == 1]
            self.assertEqual({r[8] for r in faces}, set(range(nfaces)))
            self.assertEqual(len({tuple(payload[n] for n in r[4:6]) for r in faces}), nfaces)
            self.assertEqual(len({tuple(CODEC.decode_blp(payload[n]).tobytes() for n in r[4:6])
                                  for r in faces}), nfaces)
            for row in selected:
                origin, = [r for r in original if (r[3], r[8]) == (row[3], row[8])]
                self.assertEqual(row[7], 17)
                for target, name in zip(row[4:7], origin[4:7]):
                    if name:
                        self.assertEqual(payload[target], self.source('turtle', name))
                    else:
                        self.assertEqual(target, '')
            hair = [r for r in rows if r[2] == sex and r[3] == 3 and r[0] >= 21000]
            self.assertEqual({(r[8], r[9]) for r in hair}, {(s, c) for s in range(styles) for c in range(4, 10)})
            self.assertEqual(len(hair), styles*6)
            for row in hair:
                self.assertEqual((row[4], row[6], row[7]), ('', '', 17))
                self.assertEqual(payload[row[5]], self.source('turtle', rf'Character\Tauren\ScalpLowerHair00_{row[9]-1:02}.blp'))
        self.assertFalse(any(r[3] == 3 and r[9] == 3 and r[0] >= 21000 for r in rows))

    def test_optional_only_face0_no_fake_aliases(self):
        rows = self.reports['optional']['optional_rows']
        self.assertEqual(sorted(r[0] for r in rows), list(range(21200, 21215)))
        self.assertEqual({(r[2], r[9]) for r in rows}, {(0, 26), (0, 27), (0, 28), (1, 18), (1, 19)})
        for sex, color in {(r[2], r[9]) for r in rows}:
            family = [r for r in rows if (r[2], r[9]) == (sex, color)]
            self.assertEqual(sorted((r[3], r[8], r[7]) for r in family), [(0, 0, 17), (1, 0, 17), (4, 0, 17)])
        primary_names = set(self.payload['primary'])
        for r in rows:
            self.assertTrue(all(n not in primary_names for n in r[4:7] if n))
        source, block = FOREST.read_dbc(self.source('turtle', 'table:CharSections'))
        source = [FOREST.decode(r, block, 'turtle') for r in source]
        for sex in (0, 1):
            originals = [r for r in source if r[1:4] == (6, sex, 0) and r[7] == 1]
            self.assertEqual(len(originals), 2)
            for offset, original in enumerate(originals):
                color = (26 if sex == 0 else 18) + offset
                body, = [r for r in rows if (r[2], r[3], r[9]) == (sex, 0, color)]
                for target, name in zip(body[4:6], original[4:6]):
                    self.assertEqual(self.payload['optional'][target], self.source('turtle', name))
        spirit, = [r for r in rows if (r[2], r[3], r[9]) == (0, 0, 28)]
        self.assertEqual(self.payload['optional'][spirit[4]],
                         self.source('turtle', r'textures\bakednpctextures\spiritwalkertaurenshop.blp'))

    def test_natural_styles233_four_new_keys_and_combined_donor11(self):
        for edition, payload in self.payload.items():
            previous = CODEC.read_numeric(self.old[edition][builder.STYLES], 8)
            actual = CODEC.read_numeric(payload[builder.STYLES], 8)
            self.assertEqual(len(actual), 233)
            self.assertEqual(actual, previous + NATURAL)
            self.assertEqual(len({r[:3] for r in actual}), len(actual))
        donor = CODEC.read_numeric((self.first / 'CharacterFacialHairStyles.delta.dbc').read_bytes(), 8)
        self.assertEqual(len(donor), 11)
        self.assertEqual(sorted(r for r in donor if r[0] == 6), NATURAL)
        self.assertEqual(len([r for r in donor if r[0] == 8]), 7)

    def test_independent_models_vertices_skin_arrays_materials_bones(self):
        for sex, label in enumerate(('Male', 'Female')):
            member = rf'Character\Tauren\{label}\Tauren{label}.m2'
            oldskins = [self.source('335', member[:-3]+f'{i:02}.skin') for i in range(3)]
            newskins = [self.payload['primary'][member[:-3]+f'{i:02}.skin'] for i in range(3)]
            check_geometry(self, self.source('turtle', member), self.source('335', member), oldskins,
                           self.payload['primary'][member], newskins, sex)
            self.assertEqual(self.payload['primary'][member], self.payload['optional'][member])
            for i in range(3):
                self.assertEqual(newskins[i], self.payload['optional'][member[:-3]+f'{i:02}.skin'])

    def test_all_blps_strict_generated_palette8_and_source_alpha_exact(self):
        for edition, payload in self.payload.items():
            for name, raw in payload.items():
                if name.lower().endswith('.blp'):
                    FOREST.validate_blp(raw)
        payload = self.payload['optional']
        generated = self.reports['optional']['generated_images']
        self.assertEqual(len(generated), 17)
        rows = self.reports['optional']['optional_rows']
        fitted = {}
        for proof in generated:
            name = proof['member']; raw = payload[name]
            self.assertEqual((raw[8], raw[10]), (1, 8), name)
            row, = [r for r in rows if name in r[4:7]]
            body, = [r for r in rows if r[3] == 0 and (r[2], r[9]) == (row[2], row[9])]
            atlas = CODEC.decode_blp(payload[body[4]]).repeat(2, 0).repeat(2, 1)
            box = ([0, 384, 256, 512] if 'FaceLower' in name else [0, 320, 256, 384]
                   if 'FaceUpper' in name else [256, 0, 512, 128] if 'NakedTorso' in name else [256, 192, 512, 320])
            expected = CODEC.crop(atlas, box)
            if 'Naked' in name:
                component = 'NakedTorsoSkin' if 'NakedTorso' in name else 'NakedPelvisSkin'
                sex = row[2]
                if (sex, component) not in fitted:
                    label = 'Female' if sex else 'Male'
                    bodies, clothes = [], []
                    for color in range(6):
                        stem = rf'Character\Tauren\{label}\Tauren{label}'
                        body_image = CODEC.decode_blp(self.source('335', stem+f'Skin00_{color:02}.blp'))
                        garment_image = CODEC.decode_blp(self.source('335', stem+f'{component}00_{color:02}.blp'))
                        bodies.append(CODEC.crop(body_image, box)[:, :, :3])
                        clothes.append(garment_image[:, :, :3])
                    limits = self.recipe['garment_limits'][label.lower()+'_'+component]
                    foreground, alpha, _ = CODEC.fit_garment(bodies, clothes, dict(mae_max=limits[0], p99_max=limits[1]))
                    fitted[sex, component] = foreground, alpha
                foreground, alpha = fitted[sex, component]
                expected[:, :, :3] = np.rint(alpha*foreground+(1-alpha)*expected[:, :, :3]).clip(0, 255).astype(np.uint8)
            reference = CODEC.encode_blp(expected)
            expected_palette, _ = builder.palette_encode(reference, allow_quantize=True)
            self.assertEqual(raw, expected_palette, name)
            for level, mip in enumerate(FOREST.validate_blp(raw)['mips']):
                np.testing.assert_array_equal(CODEC.decode_blp(raw, level)[:, :, 3],
                                              CODEC.decode_blp(reference, level)[:, :, 3])

    def test_publication_updates_only_known_server_donor_manifest_and_refuses_foreign(self):
        with tempfile.TemporaryDirectory(prefix='tauren-publish-') as temp:
            root = Path(temp)
            manifest = json.loads((self.first/'server-manifest.json').read_text())
            key = 'turtle-customizations/dbc/CharacterFacialHairStyles.dbc'
            manifest['files'][key].update(size=245, sha256='32cb5d24ac98286aeba6aa20952852fd5b25afd97e39cd6035c499a7f8ba16cf')
            path = root/'data/server/manifest.json'
            path.parent.mkdir(parents=True)
            donor = root/'data/server'/key
            donor.parent.mkdir(parents=True)
            combined = CODEC.read_numeric((self.first/'CharacterFacialHairStyles.delta.dbc').read_bytes(),8)
            donor.write_bytes(CODEC.numeric_dbc([r for r in combined if r[0] == 8],8))
            self.assertEqual(FOREST.sha(donor), manifest['files'][key]['sha256'])
            manifest['files'][key]['path'] = 'dbc/foreign.dbc'
            builder.write_json(path,manifest)
            with patch.object(builder,'ROOT',root):
                with self.assertRaisesRegex(ValueError,'Unknown server donor manifest'):
                    builder.publish(self.first)
                self.assertFalse((root/'client_patches/Data/patch-S.MPQ').exists())
                manifest['files'][key]['path'] = 'dbc/CharacterFacialHairStyles.dbc'
                builder.write_json(path,manifest)
                builder.publish(self.first)
                builder.publish(self.first)
            self.assertEqual(path.read_bytes(),(self.first/'server-manifest.json').read_bytes())
            self.assertEqual(donor.read_bytes(),(self.first/'CharacterFacialHairStyles.delta.dbc').read_bytes())
            for edition, target in (('primary',root/'client_patches'),
                                    ('optional',root/'client_patches/optional-extra-skins')):
                for name in builder.PRODUCTS:
                    self.assertEqual((target/name).read_bytes(),(self.first/edition/name).read_bytes())

    def test_private_mysql_apply_repeat_prerequisites_conflicts_and_rollback(self):
        """Run actual generated SQL; never use a login path or --force."""
        base_report = json.loads((ROOT / self.recipe['bases']['primary']['path'] / 'report.json').read_text())
        troll = base_report['sql_rows'] + [[r['target_id'], r['race'], r['sex'], r['base'], *r['textures'],
                                          r['flags'], r['variation'], r['color']] for r in base_report['source_to_target']]
        self.assertEqual(len(troll), 298)
        primary = self.reports['primary']['primary_rows']
        optional = self.reports['optional']['optional_rows']
        sentinel = mysql_fixture.SENTINEL
        with tempfile.TemporaryDirectory(prefix='tau-sql-') as temp:
            output = Path(temp); datadir = output / 'mysql'; datadir.mkdir()
            socket = output / 'm.sock'
            common = ['/usr/sbin/mysqld', '--no-defaults', '--datadir='+str(datadir),
                      '--user='+pwd.getpwuid(os.getuid()).pw_name, '--innodb-buffer-pool-size=32M',
                      '--innodb-redo-log-capacity=8M']
            mysql_fixture.checked([*common, '--initialize-insecure'])
            process = subprocess.Popen([*common, '--skip-networking', '--mysqlx=OFF', '--socket='+str(socket),
                                        '--pid-file='+str(output/'mysql.pid'), '--log-error='+str(output/'mysql.log')],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                db = mysql_fixture.Fixture(socket, output)
                for _ in range(120):
                    if mysql_fixture.execute(db.command[:-1], input='SELECT 1;', env=db.env).returncode == 0:
                        break
                    self.assertIsNone(process.poll()); time.sleep(.5)
                else:
                    self.fail('Private mysqld startup timed out')
                mysql_fixture.checked(db.command[:-1], input='CREATE DATABASE acore_world CHARACTER SET utf8mb4;', env=db.env)
                self.assertEqual(db.query('SELECT @@skip_networking;').strip(), '1')
                self.assertEqual(Path(db.query('SELECT @@datadir;').strip()).resolve(), datadir)
                self.assertEqual(db.query('SELECT @@socket;').strip(), str(socket))
                self.assertEqual(db.query("SHOW VARIABLES LIKE 'mysqlx_port';").strip(), '')
                self.assertNotIn('--force', db.command)
                ddl = ('CREATE TABLE charsections_dbc (' + ','.join('`'+c+'` '+
                       ('VARCHAR(100) NOT NULL' if c.startswith('Texture') else 'INT UNSIGNED NOT NULL')
                       for c in mysql_fixture.COLUMNS) + ', PRIMARY KEY (`Id`)) ENGINE=MyISAM;')

                def state(rows):
                    self.assertEqual(db.snapshot(), sorted([sentinel] + rows))

                for mode in ('STRICT_TRANS_TABLES', 'STRICT_TRANS_TABLES,NO_BACKSLASH_ESCAPES'):
                    db.reset(ddl)
                    db.query(mysql_fixture.insert(troll))

                    def run(name, error=None):
                        path = self.first / (name+'.sql')
                        routine = 'azerothcore_setup_tauren_' + ('extra_skins' if name.startswith('optional') else 'primary')
                        rollback = self.first / ('optional-rollback.sql' if name.startswith('optional') else 'primary-rollback.sql')
                        with patch.multiple(mysql_fixture, ROLLBACK=rollback, PROCEDURE=routine):
                            db.canonical(path, mode, name, error, engine_after='InnoDB')

                    # Principal is independently applicable; optional is not.
                    db.reset(ddl)
                    run('optional', 'exact principal prerequisites')
                    run('primary'); state(primary)
                    run('optional', 'exact principal prerequisites')
                    run('primary-rollback'); state([])
                    db.query(mysql_fixture.insert(troll))
                    run('optional', 'exact principal prerequisites')
                    run('primary'); state(troll+primary)
                    self.assertEqual(len(db.snapshot())-1, 491)
                    run('primary'); state(troll+primary)
                    # Exact prerequisite fields, not merely counts/IDs, are required.
                    for prerequisite in (troll[0], troll[-1], primary[0], primary[-1]):
                        db.query(f'DELETE FROM charsections_dbc WHERE Id={prerequisite[0]};')
                        run('optional', 'exact principal prerequisites')
                        db.query(mysql_fixture.insert([prerequisite]))
                        for index in (4, 5, 6):
                            original = prerequisite[index]
                            for changed in ([original.swapcase()] if original else []) + [original+' ']:
                                column = mysql_fixture.COLUMNS[index]
                                db.query(f'UPDATE charsections_dbc SET `{column}`={mysql_fixture.literal(changed)} WHERE Id={prerequisite[0]};')
                                run('optional', 'exact principal prerequisites')
                                db.query(f'UPDATE charsections_dbc SET `{column}`={mysql_fixture.literal(original)} WHERE Id={prerequisite[0]};')
                    run('optional'); state(troll+primary+optional)
                    self.assertEqual(len(db.snapshot())-1, 506)
                    run('optional'); state(troll+primary+optional)
                    run('primary-rollback', 'Remove optional skins')
                    run('optional-rollback'); state(troll+primary)
                    run('optional-rollback'); state(troll+primary)
                    run('primary-rollback'); state(troll)
                    run('primary-rollback'); state(troll)
                    # Late-row collisions prove transaction-wide refusal, on both
                    # apply and rollback, before any partial mutation can survive.
                    for name, owned, baseline in (('primary', primary, troll), ('optional', optional, troll+primary)):
                        if name == 'optional':
                            run('primary')
                        row = owned[-1]
                        for kind in ('id', 'tuple', 'case'):
                            bad = list(row)
                            if kind == 'id': bad[7] ^= 1
                            if kind == 'tuple': bad[0] = 30001
                            if kind == 'case':
                                index = next(i for i in (4, 5, 6) if bad[i])
                                bad[index] = bad[index].swapcase()
                            db.query(mysql_fixture.insert([bad]))
                            error = 'semantic tuple occupied' if kind == 'tuple' else 'owned ID has different fields'
                            run(name, error); run(name+'-rollback', error)
                            state(baseline+[bad])
                            db.query(f'DELETE FROM charsections_dbc WHERE Id={bad[0]};')
                        state(baseline)
                        run(name)
                        # Conflicts after installation must preserve all other
                        # owned rows too, especially on a refused rollback.
                        for index, value in ((7, row[7] ^ 1), (9, 253)):
                            db.query(f'UPDATE charsections_dbc SET `{mysql_fixture.COLUMNS[index]}`={value} WHERE Id={row[0]};')
                            run(name, 'owned ID has different fields')
                            run(name+'-rollback', 'owned ID has different fields')
                            db.query(f'UPDATE charsections_dbc SET `{mysql_fixture.COLUMNS[index]}`={row[index]} WHERE Id={row[0]};')
                        for texture_index in (4, 5, 6):
                            original = row[texture_index]
                            for changed in ([original.swapcase()] if original else []) + [original+' ']:
                                column = mysql_fixture.COLUMNS[texture_index]
                                db.query(f'UPDATE charsections_dbc SET `{column}`={mysql_fixture.literal(changed)} WHERE Id={row[0]};')
                                run(name, 'owned ID has different fields')
                                run(name+'-rollback', 'owned ID has different fields')
                                db.query(f'UPDATE charsections_dbc SET `{column}`={mysql_fixture.literal(original)} WHERE Id={row[0]};')
                        foreign = list(row); foreign[0] = 30001
                        db.query(mysql_fixture.insert([foreign]))
                        run(name, 'semantic tuple occupied')
                        run(name+'-rollback', 'semantic tuple occupied')
                        db.query('DELETE FROM charsections_dbc WHERE Id=30001;')
                        state(baseline+owned)
                        run(name+'-rollback'); state(baseline)
                    run('primary-rollback'); state(troll)
                self.assertEqual(db.query("SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA='acore_world';").strip(), '0')
                print(f'Private Tauren SQL: {len(db.runs)} canonical executions, two SQL modes; 298→491→506→491→298 (+ sentinel).')
            finally:
                if process.poll() is None:
                    process.terminate()
                    try: process.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.wait()


if __name__ == '__main__':
    unittest.main()
