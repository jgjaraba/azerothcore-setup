#!/usr/bin/env python3
"""Codec/contract tests; TROLL_CUSTOMIZATIONS_INTEGRATION=1 builds twice.

TROLL_CUSTOMIZATIONS_MYSQL=1 also runs real SQL in a fresh network-disabled
private mysqld with a self-contained fixture schema. No DEV DB connections.
"""
import json
import os
from pathlib import Path
import pwd
import shutil
import struct
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np

import build_troll_customizations as builder
import build_forest_troll_skins as forest


def palette_blp(depth, values):
    # Independent fixture encoder, including deliberately misleading palette A.
    width, height = 4, 2
    indices = bytes(range(8))
    palette = b''.join(bytes((i, (20 + i) % 256, (50 + i) % 256, 7)) for i in range(256))
    plane = bytearray((8 * depth + 7) // 8)
    if depth:
        for i, value in enumerate(values):
            plane[i // (8 // depth)] |= value << ((i % (8 // depth)) * depth)
    data = indices + plane
    return (struct.pack('<4sI4B2I', b'BLP2', 1, 1, depth, 0, 0, width, height)
            + struct.pack('<16I', 1172, *([0] * 15))
            + struct.pack('<16I', len(data), *([0] * 15)) + palette + data)


class CodecTests(unittest.TestCase):
    def test_palette_separate_alpha_all_depths(self):
        for depth in (0, 1, 4, 8):
            with self.subTest(depth=depth):
                maximum = (1 << depth) - 1
                values = [i % (maximum + 1) for i in range(8)]
                rgba = builder.decode_blp(palette_blp(depth, values)).reshape(-1, 4)
                self.assertEqual(rgba[:, :3].tolist(), [[50 + i, 20 + i, i] for i in range(8)])
                expected = [v * 255 // maximum for v in values] if depth else [255] * 8
                self.assertEqual(rgba[:, 3].tolist(), expected)

    def test_bgra_encoder_independent_mip_reader(self):
        rgba = np.random.default_rng(431).integers(0, 256, (8, 16, 4), dtype=np.uint8)
        raw = builder.encode_blp(rgba)
        self.assertEqual(raw[8:12], bytes((3, 8, 0, 1)))
        offsets, sizes = struct.unpack_from('<16I', raw, 20), struct.unpack_from('<16I', raw, 84)
        current = rgba
        for i in range(5):
            h, w = current.shape[:2]
            self.assertEqual(sizes[i], h * w * 4)
            actual = np.frombuffer(raw[offsets[i]:offsets[i] + sizes[i]], np.uint8).reshape(h, w, 4)
            np.testing.assert_array_equal(actual[:, :, [2, 1, 0, 3]], current)
            np.testing.assert_array_equal(builder.decode_blp(raw, i), current)
            if h == w == 1:
                break
            reduced = []
            for y in range(max(1, h // 2)):
                row = []
                for x in range(max(1, w // 2)):
                    pixels = [current[min(2*y+dy, h-1), min(2*x+dx, w-1)].astype(np.uint16)
                              for dy in (0, 1) for dx in (0, 1)]
                    row.append((sum(pixels) + 2) // 4)
                reduced.append(row)
            current = np.asarray(reduced, dtype=np.uint8)
        self.assertEqual(builder.encode_blp(rgba), raw)

    def test_reject_bad_palette_bounds_and_generated_dimensions(self):
        raw = palette_blp(8, range(8))
        with self.assertRaises(ValueError):
            builder.decode_blp(raw[:-1])
        with self.assertRaises(ValueError):
            builder.encode_blp(np.zeros((3, 4, 4), dtype=np.uint8))

    def test_pinned_source_eof_tail_shapes_preserved_and_bad_variants_rejected(self):
        for width, height, last in ((128,64,6), (128,32,5)):
            with self.subTest(dimensions=(width,height)):
                offsets, sizes, chunks, off = [0]*16, [0]*16, [], 1172
                for i in range(last+1):
                    n = max(1,width >> i) * max(1,height >> i)
                    chunk = bytes(n) + bytes([137])*n
                    offsets[i], sizes[i] = off, len(chunk)
                    off += len(chunk)
                    chunks.append(chunk)
                offsets[last+1], sizes[last+1], sizes[15] = off, (-off) & 0xffffffff, sizes[0]
                raw = (struct.pack('<4sI4B2I', b'BLP2',1,1,8,8,1,width,height)
                       + struct.pack('<16I',*offsets) + struct.pack('<16I',*sizes)
                       + bytes(1024) + b''.join(chunks))
                before = bytes(raw)
                info = builder.validate_blp(raw)
                self.assertEqual(info['source_missing_terminal_mip']['level'], last+1)
                with self.assertRaisesRegex(ValueError, 'outside explicit facial repair allowlist'):
                    builder.prepare_texture(raw)
                repaired, repaired_info, metadata = builder.prepare_texture(raw, allow_repair=True)
                self.assertEqual(metadata['source_original_sha256'], forest.digest(raw))
                self.assertFalse(metadata['byte_exact'])
                self.assertEqual(repaired[8], 3)
                self.assertEqual(repaired_info, forest.validate_blp(repaired))
                self.assertEqual((repaired_info['mips'][-1]['width'], repaired_info['mips'][-1]['height']), (1,1))
                np.testing.assert_array_equal(builder.decode_blp(repaired), builder.decode_blp(raw))
                for level in range(last+1):
                    self.assertTrue(np.all(builder.decode_blp(raw,level)[:,:,3] == 137))
                self.assertEqual(raw, before)
                with self.assertRaises(ValueError):
                    builder.decode_blp(raw,last+1)
                for pos,value in ((84,1), (84+4*(last+1),123),
                                  (20+4*(last+2),len(raw)), (84+4*15,42)):
                    bad = bytearray(raw)
                    struct.pack_into('<I',bad,pos,value)
                    with self.assertRaises(ValueError):
                        builder.validate_blp(bytes(bad))

    def test_largest_component_and_dilation(self):
        mask = np.zeros((8, 9), dtype=bool)
        mask[2:4, 3:5] = True
        mask[6, 7] = True
        support, sizes = builder.largest_support(mask)
        expected = np.zeros_like(mask)
        expected[1:5, 2:6] = True
        np.testing.assert_array_equal(support, expected)
        self.assertEqual(sizes, [4, 1])

    def test_garment_fit_known_foreground(self):
        bodies = np.stack([np.full((128, 256, 3), 20 + i*25, np.float64) for i in range(6)])
        alpha = np.zeros((128, 256, 1))
        alpha[30:80, 40:200] = 1
        underwear = bodies * (1 - alpha) + alpha * np.array([60., 70., 80.])
        foreground, fitted_alpha, proof = builder.fit_garment(bodies, underwear,
                                                              dict(mae_max=1e-8, p99_max=1e-8))
        np.testing.assert_allclose(fitted_alpha, alpha)
        np.testing.assert_allclose(foreground[40, 80], [60, 70, 80])
        self.assertEqual(proof['nonzero_alpha_pixels'], 8000)

    def test_sql_has_own_routines_exact_guards_no_update(self):
        row = (20100, 8, 0, 0, 'Character\\Custom\\TurtleTroll\\test.blp', '', '', 17, 0, 24)
        for rollback in (False, True):
            sql = builder.render_sql([row], rollback)
            self.assertIn('troll_customizations_expected', sql)
            self.assertIn('azerothcore_setup_troll_customizations', sql)
            self.assertNotIn('BINARY a.', sql)
            self.assertIn('CAST(a.`TexturePath1` AS BINARY)', sql)
            self.assertIn('a.`Flags` <=> e.`Flags`', sql)
            self.assertNotIn('UPDATE ', sql)
            self.assertIn('ROLLBACK; RESIGNAL', sql)


@unittest.skipUnless(os.environ.get('TROLL_CUSTOMIZATIONS_INTEGRATION') == '1', 'Pinned-client integration opt-in')
class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='troll-tests-')
        cls.base = Path(cls.temp.name)
        cls.first, cls.second = cls.base / 'first', cls.base / 'second'
        cls.report = builder.build(cls.first)
        time.sleep(1.1)
        cls.report2 = builder.build(cls.second)
        cls.patch = cls.first / 'Data/patch-S.MPQ'
        cls.charsections = cls.extract('DBFilesClient\\CharSections.dbc')
        cls.rows, cls.strings = forest.read_dbc(cls.charsections)
        cls.byid = {r[0]: r for r in cls.rows}

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def extract(cls, member, archive=None):
        return forest.extract(archive or cls.patch, member, cls.base / 'extract')

    def test_two_builds_all_products_identical(self):
        for name in ('Data/patch-S.MPQ', 'report.json', 'SHA256SUMS', 'CharSections.delta.dbc',
                     'CharacterFacialHairStyles.dbc', 'turtle_troll_customizations.sql', 'rollback.sql'):
            self.assertEqual((self.first / name).read_bytes(), (self.second / name).read_bytes(), name)

    def test_native_preservation_and_117_only_flag_changes(self):
        raw = self.extract('DBFilesClient\\CharSections.dbc', Path('/home/dev/wow-335/Data/esES/patch-eses-3.mpq'))
        native, strings = forest.read_dbc(raw)
        changes = []
        for row in native:
            actual = self.byid[row[0]]
            if row != actual:
                changes.append(row[0])
                self.assertEqual(row[:7] + row[8:], actual[:7] + actual[8:])
                self.assertEqual(actual[7], row[7] | 1)
                self.assertEqual((row[1], row[3]), (8, 3))
                self.assertIn(row[8], range(6 if row[2] == 0 else 5, 10))
                self.assertEqual(row[7], 0x12 if row[9] < 10 else 0x06)
        self.assertEqual(len(changes), 117)
        self.assertTrue(self.strings.startswith(strings))
        self.assertEqual(len(self.rows), 9295)
        self.assertEqual([forest.key(r) for r in self.rows], sorted(forest.key(r) for r in self.rows))
        self.assertEqual(len({r[0] for r in self.rows}), 9295)

    def test_accepted90_paths_records_and162_original_bytes(self):
        target = forest.ROOT / 'client_patches/turtle_forest_troll'
        v1 = target / 'v1' if (target / 'v1').exists() else target
        pins = json.loads(builder.MANIFEST.read_text())['v1']
        builder.verify_publication(v1, pins)
        oldreport = json.loads((v1 / 'report.json').read_text())
        self.assertEqual(self.report['source_to_target'], oldreport['source_to_target'])
        oldraw = self.extract('DBFilesClient\\CharSections.dbc', v1 / 'Data/patch-S.MPQ')
        oldrows, oldstrings = forest.read_dbc(oldraw)
        for row in oldrows:
            if 20000 <= row[0] <= 20089:
                self.assertEqual(row, self.byid[row[0]])
        self.assertTrue(self.strings.startswith(oldstrings))
        self.assertEqual(len(oldreport['resources']), 162)
        for resource in oldreport['resources']:
            self.assertEqual(self.extract(resource['member']), self.extract(resource['member'], v1 / 'Data/patch-S.MPQ'))

    def test_skin_family_fixed_faces_body_exactness_and_garment_proof(self):
        new = self.report['new_rows']
        self.assertEqual([r[0] for r in new], list(range(20100, 20347)))
        self.assertEqual(len([r for r in new if r[3] in (0, 1, 4)]), 156)
        for mapping in self.report['body_mappings']:
            sex, color = mapping['sex'], mapping['color']
            rows = [r for r in new if r[2] == sex and r[9] == color and r[3] in (0, 1, 4)]
            self.assertEqual(len(rows), 7 + sex)
            faces = [r for r in rows if r[3] == 1]
            self.assertEqual([r[8] for r in faces], list(range(5 + sex)))
            self.assertEqual(len({tuple(r[4:7]) for r in faces}), 1)
            self.assertTrue(all(r[7] == 17 for r in rows))
            spec = self.report['inputs'][mapping['source_archive']]
            source = Path('/home/dev/wow-' + ('335' if spec['client'] == '335' else 'turtle')) / spec['path']
            original = self.extract(mapping['source_member'], source)
            self.assertEqual(original, self.extract(mapping['member']))
            atlas = builder.decode_blp(original)
            if atlas.shape[0] == 256:
                atlas = atlas.repeat(2, 0).repeat(2, 1)
            for member, box in zip(faces[0][4:6], ((0,384,256,512), (0,320,256,384))):
                np.testing.assert_array_equal(builder.decode_blp(self.extract(member)), builder.crop(atlas, box))
        for proof in self.report['garment_reconstruction']:
            self.assertLessEqual(proof['mean_abs'], 3.5)
            self.assertLessEqual(proof['p99_abs'], 18.1)
            self.assertGreater(proof['nonzero_alpha_pixels'], 6000)
        alias = self.report['body_aliases'][0]
        self.assertEqual((alias['source_number'], alias['target_id'], alias['color']), (109,20000,18))

    def test_facial_alpha_dk_aliases_natural_styles_and_scope(self):
        new = self.report['new_rows']
        facials = [r for r in new if r[3] == 2]
        self.assertEqual(len(facials), 91)
        for sex, variations in ((0, (11,12,13)), (1, (6,7,8,9))):
            for var in variations:
                rows = {r[9]: r for r in facials if r[2] == sex and r[8] == var}
                self.assertEqual(set(rows), set(range(13)))
                for target, source in ((10,8),(11,8),(12,9)):
                    self.assertEqual(rows[target][4:7], rows[source][4:7])
        alpha_seen = set()
        for resource in self.report['resources']:
            if resource.get('source_archive') == 'female_textures' and '\\Female\\' not in resource['member']:
                raw = self.extract(resource['member'])
                self.assertEqual(raw[9], 8)
                alpha = builder.decode_blp(raw)[:, :, 3]
                # Some authored slots are entirely transparent. Check the real
                # separate plane directly rather than requiring paint in each.
                original = self.extract(resource['source_member'], Path('/home/dev/wow-turtle/Data/patch-5.mpq'))
                off = struct.unpack_from('<I', original, 20)[0]
                expected_alpha = np.frombuffer(original, np.uint8, alpha.size, off + alpha.size)
                np.testing.assert_array_equal(alpha.flatten(), expected_alpha)
                alpha_seen.update(map(int, np.unique(alpha)))
                if resource.get('repair_type'):
                    np.testing.assert_array_equal(builder.decode_blp(raw), builder.decode_blp(original))
                else:
                    self.assertEqual(raw, original)
                self.assertEqual(forest.digest(raw), resource['sha256'])
        self.assertTrue({0, 255}.issubset(alpha_seen))
        self.assertGreater(len(alpha_seen), 200)
        natural = builder.read_numeric(self.extract('DBFilesClient\\CharacterFacialHairStyles.dbc'), 8)
        compact = builder.read_numeric((self.first / 'CharacterFacialHairStyles.dbc').read_bytes(), 8)
        self.assertEqual(len(natural), 229)
        self.assertEqual(len(compact), 7)
        self.assertEqual(natural[-7:], compact)
        native = builder.read_numeric(self.extract('DBFilesClient\\CharacterFacialHairStyles.dbc',
                                                  Path('/home/dev/wow-335/Data/esES/patch-eses.mpq')), 8)
        self.assertEqual(natural[:222], native)
        self.assertEqual([r[4] for r in compact], [2,4,6,2,3,4,5])
        members = set(self.report['mpq_members'])
        self.assertEqual(len(members), 306)
        self.assertTrue(all(n.startswith('Character\\Custom\\') or n in (
            'DBFilesClient\\CharSections.dbc', 'DBFilesClient\\CharacterFacialHairStyles.dbc') for n in members))
        self.assertEqual(len(builder.read_numeric((self.first / 'CharacterFacialHairStyles.dbc').read_bytes(), 8)), 7)
        delta, _ = forest.read_dbc((self.first / 'CharSections.delta.dbc').read_bytes())
        self.assertEqual(len(delta), 364)

    def test_provenance_and_manifest_inputs(self):
        self.assertEqual(self.report['manifest_sha256'], forest.sha(builder.MANIFEST))
        self.assertTrue(all('work/' not in p['member'] and len(p['sha256']) == 64
                            for p in self.report['provenance']))
        for r in self.report['resources']:
            self.assertEqual(forest.digest(self.extract(r['member'])), r['sha256'])

    def test_all_published_blps_strict_valid_and_exactly_two_pixel_exact_repairs(self):
        repairs = []
        manifest = json.loads(builder.MANIFEST.read_text())
        for resource in self.report['resources']:
            raw = self.extract(resource['member'])
            info = forest.validate_blp(raw)  # Never the tolerant source validator.
            if resource.get('source_member'):
                spec = self.report['inputs'][resource['source_archive']]
                root = Path('/home/dev/wow-' + ('335' if spec['client'] == '335' else 'turtle'))
                original = self.extract(resource['source_member'], root / spec['path'])
                self.assertEqual(resource['source_original_sha256'], forest.digest(original))
                if resource.get('repair_type'):
                    repairs.append(resource['source_member'])
                    self.assertFalse(resource['byte_exact'])
                    self.assertEqual(resource['repair_type'], 'terminal_mip_rebuild_encoding3_bgra')
                    self.assertIn('source_missing_terminal_mip', resource)
                    self.assertTrue(resource['generated_full_mips'])
                    self.assertEqual(info['encoding'], 3)
                    self.assertEqual((info['mips'][-1]['width'],info['mips'][-1]['height']), (1,1))
                    np.testing.assert_array_equal(builder.decode_blp(raw), builder.decode_blp(original))
                    with self.assertRaises(ValueError):
                        forest.validate_blp(original)
                else:
                    self.assertTrue(resource['byte_exact'])
                    self.assertEqual(raw, original)
        self.assertEqual(sorted(repairs), sorted(manifest['repair_terminal_mips']))
        self.assertEqual(len(repairs), 2)

    def test_publish_preserves_v1_refuses_unknown_and_is_repeatable(self):
        published = forest.ROOT / 'client_patches/turtle_forest_troll'
        source = published / 'v1' if (published / 'v1').exists() else published
        target = self.base / 'publication'
        shutil.copytree(source, target)
        # Redirect canonical owned server/SQL destinations into the test tree.
        with patch.object(builder, 'ROOT', self.base / 'sandbox'):
            builder.publish(self.first, target)
            builder.publish(self.second, target)
            builder.verify_publication(target / 'v1', json.loads(builder.MANIFEST.read_text())['v1'])
            builder.verify_publication(target)
            self.assertEqual(set(p.name for p in target.iterdir()), {'Data','report.json','SHA256SUMS','v1'})
            # The MPQ alone is insufficient: tampering with an otherwise matching
            # report must not satisfy either generated or pinned-prior identity.
            real_report = (target / 'report.json').read_bytes()
            fake_report = json.loads(real_report)
            fake_report['feature'] = 'unknown publication'
            (target / 'report.json').write_text(json.dumps(fake_report))
            (target / 'SHA256SUMS').write_text(''.join(f'{forest.sha(target / n)}  {n}\n'
                                                     for n in ('Data/patch-S.MPQ','report.json')))
            with self.assertRaisesRegex(ValueError, 'Refusing unknown current patch-S'):
                builder.publish(self.first, target)
            (target / 'report.json').write_bytes(real_report)
            (target / 'SHA256SUMS').write_text(''.join(f'{forest.sha(target / n)}  {n}\n'
                                                     for n in ('Data/patch-S.MPQ','report.json')))
            before = {p.relative_to(target): p.read_bytes() for p in target.rglob('*') if p.is_file()}
            staging = target / 'report.json.tmp'
            staging.write_bytes(b'stale foreign staging file')
            with patch.object(builder.shutil, 'copyfile', wraps=shutil.copyfile) as copier:
                with self.assertRaisesRegex(ValueError, 'Stale publish staging file'):
                    builder.publish(self.first, target)
                # Detect even an early replacement with identical bytes.
                copier.assert_not_called()
            self.assertEqual(before, {p.relative_to(target): p.read_bytes() for p in target.rglob('*')
                                      if p.is_file() and p != staging})
            self.assertFalse((target / 'Data/patch-S.MPQ.tmp').exists())
            staging.unlink()
            (target / 'Data/patch-S.MPQ').write_bytes(b'unknown')
            with self.assertRaises(ValueError):
                builder.publish(self.first, target)
            # A self-consistent foreign report/checksum cannot bless an unknown MPQ.
            fake = json.loads((target / 'report.json').read_text())
            fake['patch_sha256'] = forest.sha(target / 'Data/patch-S.MPQ')
            (target / 'report.json').write_text(json.dumps(fake))
            (target / 'SHA256SUMS').write_text(''.join(f'{forest.sha(target / n)}  {n}\n'
                                                     for n in ('Data/patch-S.MPQ','report.json')))
            with self.assertRaisesRegex(ValueError, 'Refusing unknown current patch-S'):
                builder.publish(self.first, target)


@unittest.skipUnless(os.environ.get('TROLL_CUSTOMIZATIONS_MYSQL') == '1', 'Private MySQL fixture opt-in')
class SQLTests(unittest.TestCase):
    def test_real_mysql_guards_roundtrip_and_preservation(self):
        import test_forest_troll_sql as fixture
        source = forest.ROOT / 'client_patches/archive/turtle_forest_troll/v2/report.json'
        report = json.loads(source.read_text())
        expected = report['sql_rows']
        accepted = [[r['target_id'], r['race'], r['sex'], r['base'], *r['textures'],
                     r['flags'], r['variation'], r['color']] for r in report['source_to_target']]
        with tempfile.TemporaryDirectory(prefix='troll-mysql-') as temp:
            output = Path(temp)
            datadir, socket = output / 'mysql', output / 'm.sock'
            datadir.mkdir()
            common = ['/usr/sbin/mysqld', '--no-defaults', '--datadir=' + str(datadir),
                      '--user=' + pwd.getpwuid(os.getuid()).pw_name,
                      '--innodb-buffer-pool-size=32M', '--innodb-redo-log-capacity=8M']
            fixture.checked([*common, '--initialize-insecure'])
            process = subprocess.Popen([*common, '--skip-networking', '--mysqlx=OFF',
                                        '--socket=' + str(socket), '--pid-file=' + str(output / 'mysql.pid'),
                                        '--log-error=' + str(output / 'mysql.log')],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                db = fixture.Fixture(socket, output)
                for _ in range(120):
                    if fixture.execute(db.command[:-1], input='SELECT 1;', env=db.env).returncode == 0:
                        break
                    self.assertIsNone(process.poll())
                    time.sleep(.5)
                else:
                    self.fail('Private MySQL startup timed out')
                fixture.checked(db.command[:-1], input='CREATE DATABASE acore_world CHARACTER SET utf8mb4;', env=db.env)
                ddl = ('CREATE TABLE charsections_dbc (' + ','.join(
                    f'`{col}` ' + ('VARCHAR(255) NOT NULL' if col.startswith('Texture') else 'INT UNSIGNED NOT NULL')
                    for col in forest.COLS) + ',PRIMARY KEY (`Id`)) ENGINE=MyISAM;')
                apply = forest.ROOT / 'data/sql/history/troll-v2-full/apply.sql'
                rollback = forest.ROOT / 'data/sql/history/troll-v2-full/rollback.sql'
                with patch.multiple(fixture, APPLY=apply, ROLLBACK=rollback,
                                    PROCEDURE='azerothcore_setup_troll_customizations'):
                    for mode in ('STRICT_TRANS_TABLES', 'STRICT_TRANS_TABLES,NO_BACKSLASH_ESCAPES'):
                        db.reset(ddl)
                        checks = []
                        fixture.suite(db, sorted(expected), mode, checks)
                        # Accepted90 + unrelated sentinel survive every new overlay operation.
                        db.query(fixture.insert(accepted))
                        baseline = sorted(accepted + [fixture.SENTINEL])
                        for path in (apply, apply, rollback, rollback):
                            db.canonical(path, mode, 'accepted-preservation-' + path.name)
                            self.assertEqual(db.snapshot(), sorted(baseline + expected) if path == apply else baseline)
                        # A pre-existing SQL hair row with native BEFORE flags is foreign.
                        hair = report['hair_changes'][0]
                        before = hair['before']
                        db.query(fixture.insert([before]))
                        db.canonical(apply, mode, 'hair-native-before-refused', 'owned ID has different fields')
                        db.canonical(rollback, mode, 'hair-before-rollback-refused', 'owned ID has different fields')
                        self.assertEqual(db.snapshot(), sorted(baseline + [before]))
                self.assertEqual(db.query('SELECT @@skip_networking;').strip(), '1')
            finally:
                process.terminate()
                try:
                    process.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == '__main__':
    unittest.main()
