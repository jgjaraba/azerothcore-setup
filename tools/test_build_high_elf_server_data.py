"""Extractor-only WDT restriction and stock/archive boundary regression tests."""
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest

from build_high_elf_server_data import (Build, ROOT, cardinal_halo, map_name, mmap_name,
                                      official, owned_collision, subset_wdt)


class ExtractionInputs(unittest.TestCase):
    def test_wdt_restricts_only_main_preserving_selected_records(self):
        main = b''.join(struct.pack('<II', 1, y * 64 + x + 100)
                        for y in range(64) for x in range(64))
        before = b'REVM' + struct.pack('<II', 4, 18)
        after = b'OMWM' + struct.pack('<I', 4) + b'abc\0'
        data = before + b'NIAM' + struct.pack('<I', len(main)) + main + after
        out = subset_wdt(data, {(33, 22), (37, 26)})
        self.assertEqual(out[:12], before)
        self.assertEqual(out[-len(after):], after)
        present = set()
        for y in range(64):
            for x in range(64):
                value = struct.unpack_from('<II', out, 20 + (y * 64 + x) * 8)
                if value[0]:
                    present.add((x, y))
                    self.assertEqual(value[1], y * 64 + x + 100)
                else:
                    self.assertEqual(value, (0, 0))
        self.assertEqual(present, {(33, 22), (37, 26)})

    def test_malformed_wdt_rejected(self):
        for data in (b'', b'NIAM' + struct.pack('<I', 32768),
                     b'NIAM' + struct.pack('<I', 4) + b'abcd'):
            with self.assertRaises((ValueError, struct.error)):
                subset_wdt(data, {(33, 22)})

    def test_snapshot_custom_archives_are_excluded(self):
        for name in ('patch-T.MPQ', 'patch-Z.mpq', 'Patch-F.mpq', 'patch-4.MPQ'):
            self.assertFalse(official(Path('/stock/Data') / name))
        for name in ('patch-enUS-Z.MPQ', 'patch-enUS-M.MPQ', 'patch-enUS-N.MPQ'):
            self.assertFalse(official(Path('/stock/Data/enUS') / name))
        for name in ('common.MPQ', 'patch.MPQ', 'patch-2.MPQ', 'patch-3.MPQ'):
            self.assertTrue(official(Path('/stock/Data') / name))
        self.assertTrue(official(Path('/stock/Data/enUS/patch-enUS-3.MPQ')))
        self.assertTrue(official(Path('/stock/Data/esES/patch-eses-3.mpq')))

    def test_halo_excludes_interior_and_diagonal_only_tiles(self):
        self.assertEqual(cardinal_halo({(33, 22), (33, 23)}),
                         {(32, 22), (34, 22), (33, 21), (32, 23), (34, 23), (33, 24)})

    def test_asymmetric_tile_coordinate_filenames(self):
        self.assertEqual(map_name(33, 22), '0002233.map')
        self.assertEqual(mmap_name(33, 22), '0002233.mmtile')

    def test_only_exact_previous_owned_custom_wmo_can_replace_collision(self):
        custom = 'vmaps/He_195A0A632Bd23Cea9A73_Highelfhousevariantb.wmo.vmo'
        native = 'vmaps/Highelf_Smallhouse01.wmo.vmo'
        owned = {custom: {'sha256': 'previous'}, native: {'sha256': 'native'}}
        self.assertTrue(owned_collision(custom, 'previous', owned))
        self.assertFalse(owned_collision(custom, 'unknown', owned))
        self.assertFalse(owned_collision(custom, 'previous', {}))
        self.assertFalse(owned_collision(native, 'native', owned))

    def test_cached_commands_reject_unacknowledged_wrapper_drift(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'work/tmp') as temp:
            args = SimpleNamespace(output=Path(temp), server=Path('/unused'), reuse_previous_wrapper=False)
            b = Build(args)
            b.run('test', ['/usr/bin/true'])
            b.wrapper_sha256 = 'changed-revision'
            with self.assertRaisesRegex(ValueError, 'another wrapper revision'):
                b.run('test', ['/usr/bin/true'])
            args.reuse_previous_wrapper = True
            b.run('test', ['/usr/bin/true'])
            self.assertTrue((b.out / 'reuse-audit.json').is_file())


if __name__ == '__main__':
    unittest.main()
