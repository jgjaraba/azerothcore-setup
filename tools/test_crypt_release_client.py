"""Synthetic, non-proprietary regression tests for release row isolation/guards."""
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import crypt_release_client as client
from crypt_release_dbc import merge_dbc, parse_dbc, semantic_row


def dbc(fields, rows, strings=b'\0'):
    return (struct.pack('<4s4I', b'WDBC', len(rows), fields, fields * 4, len(strings))
            + b''.join(struct.pack(f'<{fields}I', *r) for r in rows) + strings)


class DbcTests(unittest.TestCase):
    def test_worldmap_preserves_ruby_excludes_104_unrelated(self):
        ruby = [609, 724, 4987, 1, 0xDEADBEEF, 2, 3, 4, 5, 6, 7]
        stock = dbc(11, [ruby], b'\0RubySanctum\0')
        modified_ruby = ruby.copy()
        modified_ruby[4] = 999
        unrelated = [[1000+i, 900+i, 0, 1, 0, 0, 0, 0, 0, 0, 0] for i in range(104)]
        pilot = [674, 800, 5086, 8, 1, 2, 3, 4, 0xFFFFFFFF, 0, 0]
        donor = dbc(11, [modified_ruby, *unrelated, pilot], b'\0custom\0KarazhanCrypt\0')
        merged = merge_dbc(stock, donor, [674], [3])
        _, rows, strings = parse_dbc(merged)
        self.assertEqual([r[0] for r in rows], [609, 674])
        self.assertEqual(rows[0], ruby)
        self.assertTrue(strings.startswith(b'\0RubySanctum\0'))
        self.assertEqual(semantic_row(rows[1], strings, [3])[3], b'KarazhanCrypt')
        self.assertEqual(merge_dbc(merged, donor, [674], [3]), merged)

    def test_strings_empty_zero_and_semantic_collision(self):
        stock = dbc(4, [[1, 1, 0, 123]], b'\0native\0')
        donor = dbc(4, [[2, 7, 0, 456]], b'\0other\0pilot\0')
        result = merge_dbc(stock, donor, [2], [1, 2])
        _, rows, block = parse_dbc(result)
        self.assertEqual(rows[1][2], 0)
        self.assertEqual(rows[1][3], 456)
        self.assertEqual(block[:8], b'\0native\0')
        shifted = dbc(4, [[2, 1, 7, 456]], b'\0pilot\0\0')
        self.assertEqual(merge_dbc(result, shifted, [2], [1, 2]), result)
        with self.assertRaisesRegex(ValueError, 'collision'):
            merge_dbc(result, dbc(4, [[2, 1, 0, 457]], b'\0pilot\0'), [2], [1, 2])

    def test_trigger_map_order_stable_and_float_bits(self):
        base = dbc(3, [[5, 0, 0x80000000], [3, 0, 0x7FC00001], [9, 724, 1]])
        donor = dbc(3, [[900800, 0, 123], [900801, 800, 456]])
        result = merge_dbc(base, donor, [900800, 900801], [], True)
        rows = parse_dbc(result)[1]
        self.assertEqual([r[0] for r in rows], [5, 3, 900800, 9, 900801])
        self.assertEqual([r for r in rows if r[0] < 10], parse_dbc(base)[1])
        self.assertEqual(merge_dbc(result, donor, [900800, 900801], [], True), result)
        with self.assertRaisesRegex(ValueError, 'ordered'):
            merge_dbc(dbc(3, [[1, 3, 0], [2, 0, 0]]), donor, [900800], [], True)

    def test_malformed_inputs_fail_closed(self):
        good = dbc(2, [[1, 0]])
        for bad in (b'', good[:-1], good+b'\0', dbc(2, [[1, 0], [1, 0]]),
                    dbc(2, [[1, 0]], b'not-null\0')):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                merge_dbc(bad, good, [1], [1])
        with self.assertRaisesRegex(ValueError, 'count mismatch'):
            merge_dbc(good, dbc(3, [[2, 0, 0]]), [2], [1])
        with self.assertRaisesRegex(ValueError, 'offset'):
            merge_dbc(good, dbc(2, [[2, 100]]), [2], [1])
        with self.assertRaisesRegex(ValueError, 'Missing donor'):
            merge_dbc(good, good, [99], [1])


class ClientTests(unittest.TestCase):
    def donor_trs(self):
        return ('unrelated\\map.blp\tcustom.blp\n' + ''.join(
            f'KarazhanCrypt\\map{i}.blp\ttw800_{i}.blp\n' for i in range(29))).encode()

    def test_trs_stock_preserved_only_pilot_aliases_and_reapply(self):
        stock = b'dir: Native\r\nNative\\map.blp\tnative.blp\r\n'
        result = client.merge_trs(stock, self.donor_trs())
        self.assertTrue(result.startswith(stock))
        self.assertEqual(len(client.parse_trs(result)), 30)
        self.assertNotIn(b'custom.blp', result)
        self.assertEqual(client.merge_trs(result, self.donor_trs()), result)
        with self.assertRaisesRegex(ValueError, 'collision'):
            client.merge_trs(b'KarazhanCrypt\\map0.blp\twrong.blp\n', self.donor_trs())
        with self.assertRaisesRegex(ValueError, '29'):
            client.merge_trs(stock, b'KarazhanCrypt\\map0.blp\tfoo.blp\n')

    def test_stock_allowlist(self):
        for path in ('common-2.MPQ', 'patch-3.MPQ', 'esES/patch-eses-3.mpq'):
            self.assertTrue(client.stock_path(path))
        for path in ('patch-Z.mpq', 'patch-T.MPQ', 'esES/patch-esES-N.MPQ', 'enUS/patch-enUS-4.MPQ'):
            self.assertFalse(client.stock_path(path))
        for path in ('../patch.MPQ', '/patch.MPQ', 'Data\\..\\patch.MPQ'):
            with self.assertRaises(ValueError):
                client.stock_path(path)

    def test_exact_preflight_unknown_extra_changed_and_loose(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / 'Data'
            data.mkdir()
            archive = data / 'patch-3.MPQ'
            archive.write_bytes(b'stock')
            manifest = dict(archives=[dict(path=archive.name, sha256=client.file_sha(archive), size=5)])
            self.assertEqual(client.preflight_client(root, manifest)['status'], 'PASS')
            for name in ('patch-Z.mpq', 'common.MPQ', 'DBFilesClient/Map.dbc', 'Textures/a.blp'):
                path = data / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'extra')
                with self.subTest(name=name), self.assertRaises(ValueError):
                    client.preflight_client(root, manifest)
                path.unlink()
            archive.write_bytes(b'other')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                client.preflight_client(root, manifest)
            archive.unlink()
            with self.assertRaises(ValueError):
                client.preflight_client(root, manifest)

    def test_archive_resolution_uses_explicit_order_not_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'Data').mkdir()
            for name in ('patch.MPQ', 'patch-3.MPQ'):
                (root / 'Data' / name).write_bytes(name.encode())
            def extract(tool, archive, name, optional=False):
                return archive.name.encode() + name.encode()
            with patch.object(client, 'extract', side_effect=extract):
                base, manifest = client.read_archive_baseline(root, ['patch-3.MPQ', 'patch.MPQ'], 'mpq')
            self.assertTrue(all(raw.startswith(b'patch.MPQ') for raw in base.values()))
            self.assertTrue(all(r['archive'] == 'patch.MPQ' for r in manifest['resources'].values()))
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                client.archive_records(root, ['patch.MPQ', 'patch.MPQ'])

    def test_fixture_hash_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fixture'
            base = {client.key(n): b'baseline' for n in client.resources()}
            manifest = dict(archives=[dict(path='patch-3.MPQ', sha256='0'*64, size=1)],
                            resources={n: dict(sha256=client.sha(raw)) for n, raw in base.items()})
            client.write_fixture(path, base, manifest)
            self.assertEqual(client.read_fixture(path), (base, manifest))
            (path / client.relative(client.key(client.TRS))).write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError, 'Fixture hash mismatch'):
                client.read_fixture(path)


@unittest.skipUnless(os.environ.get('CRYPT_RELEASE_INTEGRATION'), 'Opt-in local proprietary fixtures')
class StockIntegrationTests(unittest.TestCase):
    def test_stock_and_art_preservation_and_determinism(self):
        root = Path(os.environ['CRYPT_RELEASE_INTEGRATION'])
        base, _ = client.read_fixture(root / 'crypt-release-stock-eses')
        first = root / 'crypt-release-client-eses-a/Data/patch-T.MPQ'
        second = root / 'crypt-release-client-eses-b/Data/patch-T.MPQ'
        self.assertEqual(first.read_bytes(), second.read_bytes())
        tool = client.ROOT / 'tools/mpq'
        actual = client.members(tool, first)
        donor = client.members(tool, root / 'client-overlay-r5/Data/patch-T.MPQ')
        for name, (_, raw) in actual.items():
            if name not in base:
                self.assertEqual(raw, donor[name][1])
        for filename, (_, ids, fields, _) in client.DBC_DELTAS.items():
            name = client.key('DBFilesClient\\' + filename)
            _, before, before_strings = parse_dbc(base[name])
            _, after, after_strings = parse_dbc(actual[name][1])
            self.assertEqual([r for r in after if r[0] not in ids],
                             [r for r in before if r[0] not in ids], filename)
            self.assertTrue(after_strings.startswith(before_strings), filename)
            self.assertEqual(set(r[0] for r in after), set(r[0] for r in before) | set(ids))
            self.assertEqual(merge_dbc(actual[name][1], donor[name][1], ids, fields,
                                      filename == 'AreaTrigger.dbc'), actual[name][1])
        name = client.key('DBFilesClient\\WorldMapArea.dbc')
        _, before, _ = parse_dbc(base[name])
        _, after, _ = parse_dbc(actual[name][1])
        _, source, _ = parse_dbc(donor[name][1])
        self.assertEqual(next(r for r in before if r[0] == 609), next(r for r in after if r[0] == 609))
        unrelated = set(r[0] for r in source) - set(r[0] for r in before) - {674}
        self.assertEqual(len(unrelated), 104)
        self.assertFalse(unrelated & set(r[0] for r in after))
        trs = actual[client.key(client.TRS)][1]
        self.assertTrue(trs.startswith(base[client.key(client.TRS)]))
        self.assertEqual(len(client.parse_trs(trs)), len(client.parse_trs(base[client.key(client.TRS)])) + 29)


if __name__ == '__main__':
    unittest.main()
