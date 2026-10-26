#!/usr/bin/env python3
"""Contract regressions for the real pinned client payloads (no server/client writes)."""
import json
from pathlib import Path
import tempfile
import unittest
import struct
from unittest.mock import patch

import consolidate_client_patches as c
from crypt_release_dbc import parse_dbc, string_at
from high_elf_eye_selectors import eye_models, fix_selectors
from test_new_races_assets import validate_eye_delta, validate_opacity_delta
from high_elf_eye_opacity import member as eye_member


class DeliveryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock = json.loads(c.LOCK.read_text())
        cls.sources = c.Sources(cls.lock)
        cls.planned = c.plan(cls.lock, cls.sources)
        cls.report = c.audit(cls.planned, cls.lock, cls.sources)

    def master(self, profile, name):
        return self.planned[profile+'/Data/patch-Z.mpq']['dbfilesclient/'+name.lower()+'.dbc']['data']

    def test_every_existing_hd_record_preserved(self):
        for member, (_, original) in self.sources.get(c.HD).items():
            if member.endswith('.dbc'):
                table = member.split('/')[-1][:-4]
                result = self.master('hd_client', table)
                diff = c.record_diff(original, result, table)
                self.assertEqual(diff['changed'], [], table)
                self.assertEqual(diff['removed'], [], table)
                if table != 'itemextendedcost':
                    self.assertEqual(result, original, table)
        root = self.planned['hd_client/Data/patch-Z.mpq']
        self.assertEqual(set(root), set(self.sources.get(c.HD)))
        self.assertEqual(len(root), 8)
        self.assertEqual(root['textures/bakednpctextures/darkrider.blp']['data'],
                         self.sources.get(c.HD)['textures/bakednpctextures/darkrider.blp'][1])
        self.assertEqual(self.master('hd_client', 'CreatureDisplayInfoExtra'),
                         self.sources.get(c.HD)['dbfilesclient/creaturedisplayinfoextra.dbc'][1])
        self.assertEqual(len(c.rows(self.master('hd_client', 'CreatureDisplayInfoExtra'),
                                    'creaturedisplayinfoextra')), 15478)

    def test_hd_costs_add_only_52_records(self):
        base = self.sources.get(c.HD)['dbfilesclient/itemextendedcost.dbc'][1]
        diff = c.record_diff(base, self.master('hd_client', 'ItemExtendedCost'), 'itemextendedcost')
        self.assertEqual(set(diff['added']), {str(i) for i in [*range(98010, 98036), *range(99010, 99036)]})
        self.assertEqual(diff['changed'], [])

    def test_spell_tables_preserved_in_full_for_both_profiles(self):
        for profile in self.lock['profiles']:
            for locale in ('enUS', 'esES'):
                package = profile+'/Data/'+locale+'/patch-'+locale+'-Z.MPQ'
                actual = self.planned[package]['dbfilesclient/spell.dbc']['data']
                original = self.sources.get('client_patches/patch-'+locale+'-Z.MPQ')['dbfilesclient/spell.dbc'][1]
                self.assertEqual(actual, original)
                self.assertEqual(len(c.rows(actual, 'spell')), 49841)

    def test_native_racial_names_survive_localization(self):
        name_fields = [*range(14, 30), *range(31, 47), *range(48, 64)]
        for profile in ('regular_client',):
            for locale in ('enUS', 'esES'):
                package = profile+'/Data/'+locale+'/patch-'+locale+'-Z.MPQ'
                actual = self.planned[package]['dbfilesclient/chrraces.dbc']['data']
                original = self.sources.get('native:'+locale+':dbfilesclient/chrraces.dbc')['dbfilesclient/chrraces.dbc'][1]
                a, b = c.rows(actual, 'chrraces'), c.rows(original, 'chrraces')
                for ident, row in b.items():
                    expected = [row[i+6] if locale == 'esES' and i in (14, 31, 48) and not row[i]
                                else row[i] for i in name_fields]
                    self.assertEqual([a[ident][i] for i in name_fields], expected)
                self.assertEqual(a[22][14], b'High Elf' if locale == 'enUS' else b'Alto Elfo')
                self.assertEqual(a[22][20], b'Alto Elfo')
                self.assertEqual(a[23][14], b'Goblin')

    def test_spanish_native_race_headings_have_translated_default_slots(self):
        package = self.planned['regular_client/Data/esES/patch-esES-Z.MPQ']
        races = c.rows(package['dbfilesclient/chrraces.dbc']['data'], 'chrraces')
        native = c.rows(self.sources.get('native:esES:dbfilesclient/chrraces.dbc')[
            'dbfilesclient/chrraces.dbc'][1], 'chrraces')
        for ident in (1, 2, 3, 4, 5, 6, 7, 8, 10, 11):
            for default, spanish in ((14, 20), (31, 37), (48, 54)):
                self.assertTrue(races[ident][default], (ident, default))
                self.assertEqual(races[ident][default], native[ident][spanish], (ident, default))

    def test_localized_tables_are_owned_only_by_locale_archives(self):
        master = self.planned['regular_client/Data/patch-Z.mpq']
        for table in ('ChrRaces', 'Map', 'AreaTable', 'MapDifficulty', 'Spell'):
            key = 'dbfilesclient/'+table.lower()+'.dbc'
            self.assertNotIn(key, master)
            for locale in ('enUS', 'esES'):
                self.assertIn(key, self.planned['regular_client/Data/'+locale+'/patch-'+locale+'-Z.MPQ'])

    def test_chr_races_client_tokens_and_numeric_contract_preserved(self):
        # Independent explicit Wrath schema: field7 is numeric TeamID; field11
        # is ClientFileString consumed by native Glue/background selection.
        string_columns = {6, 11, *range(14, 30), *range(31, 47), *range(48, 64), 65, 66, 67}
        _, donor_rows, donor_strings = parse_dbc(self.sources.get(c.NEW)['dbfilesclient/chrraces.dbc'][1])
        donor = {r[0]: r for r in donor_rows}
        for locale in ('enUS', 'esES'):
            package = 'regular_client/Data/'+locale+'/patch-'+locale+'-Z.MPQ'
            _, output, strings = parse_dbc(self.planned[package]['dbfilesclient/chrraces.dbc']['data'])
            for row in output:
                original = donor[row[0]]
                for col in (6, 11, 65, 66, 67):
                    self.assertEqual(string_at(strings, row[col]), string_at(donor_strings, original[col]),
                                     f'{locale} race={row[0]} nonlocalized string column={col}')
                for col in set(range(69)) - string_columns:
                    self.assertEqual(row[col], original[col], f'{locale} race={row[0]} numeric column={col}')

    def test_primary_assets_and_normalized_new_races_preserved(self):
        for profile in ('regular_client',):
            package = self.planned[profile+'/Data/patch-S.MPQ']
            for source in (c.PRIMARY, c.NEW):
                for member, (_, original) in self.sources.get(source).items():
                    if member.startswith('character/'):
                        if source == c.NEW and member in {eye_member(s).lower() for s in ('Male', 'Female')}:
                            validate_opacity_delta(original, package[member]['data'],
                                                   'Male' if '/male/' in member else 'Female')
                        else:
                            self.assertEqual(package[member]['data'], original, member)
            self.assertEqual(len(self.report['new_race_closure'][profile]['mdx_to_m2']), 4)
            self.assertGreater(self.report['new_race_compositor'][profile]['textures'], 44)
        spec = self.lock['sources'][c.PRIMARY]
        self.assertEqual(c.file_sha(c.ROOT/spec['path']), spec['sha256'])

    def test_high_elf_selectors_exact_frozen_delta_and_model_contract(self):
        key = 'dbfilesclient/characterfacialhairstyles.dbc'
        before = self.sources.get(c.NEW)[key][1]
        after = self.master('regular_client', 'CharacterFacialHairStyles')
        validate_eye_delta(before, after)
        payload = {k: e['data'] for k, e in self.planned['regular_client/Data/patch-S.MPQ'].items()}
        geometry, report = eye_models(payload)
        self.assertEqual(fix_selectors(before, geometry), after)
        self.assertEqual(fix_selectors(after, geometry), after)
        self.assertEqual([report[s]['section_index'] for s in ('Male', 'Female')], [53, 5])
        for sex in ('Male', 'Female'):
            base = f'character/custom/turtlehighelf/{sex}/turtlehighelf{sex}'.lower()
            for suffix in ('.m2', '00.skin'):
                original = self.sources.get(c.NEW)[base+suffix][1]
                if suffix == '.m2':
                    validate_opacity_delta(original, payload[base+suffix], sex)
                else:
                    self.assertEqual(payload[base+suffix], original)
            broken = dict(payload)
            skin = bytearray(broken[base+'00.skin'])
            _, offset = struct.unpack_from('<2I', skin, 28)
            struct.pack_into('<H', skin, offset+report[sex]['section_index']*48, 1700)
            broken[base+'00.skin'] = bytes(skin)
            with self.assertRaisesRegex(ValueError, 'exactly one.*1702'):
                eye_models(broken)
            broken = dict(payload)
            model = bytearray(broken[base+'.m2'])
            count, offset = struct.unpack_from('<2I', model, 112)
            model[offset:offset+count*4] = bytes(count*4)
            broken[base+'.m2'] = bytes(model)
            with self.assertRaisesRegex(ValueError, 'unlit/additive'):
                eye_models(broken)

    def test_all_frozen_inputs_exist_without_active_historical_paths(self):
        for source, spec in self.lock['sources'].items():
            self.assertTrue((c.ROOT/spec['path']).is_file(), source)
            if not source.startswith('native:'):
                self.assertTrue(spec['path'].startswith('client_patches/archive/'), source)
                self.assertFalse((c.ROOT/source).exists(), source)
        self.assertTrue(c.pinned_path('launcher', self.lock['launcher']).is_file())
        self.assertTrue(self.lock['launcher']['path'].startswith('client_patches/archive/'))

    def test_optional_and_historical_packages_never_consumed(self):
        for package in self.planned.values():
            for member in package.values():
                for source in member['provenance']:
                    self.assertNotIn('optional', source)
                    self.assertNotIn('face-format-test', source)
                    self.assertNotIn(source, self.lock['excluded_inventory'])
        receipt = json.loads((c.ROOT/'client_patches/archive/relocations.json').read_text())
        for source, entry in receipt.items():
            self.assertFalse((c.ROOT/source).exists())
            dest = c.ROOT/entry['destination']
            actual = {str(p.relative_to(dest)): c.file_sha(p) for p in dest.rglob('*') if p.is_file()}
            self.assertEqual(actual, entry['files'])

    def test_hd_conservative_profile_does_not_override_external_baseline(self):
        self.assertEqual({p for p in self.planned if p.startswith('hd_client/')}, {
            'hd_client/Data/patch-Z.mpq', 'hd_client/Data/enUS/patch-enUS-Z.MPQ',
            'hd_client/Data/esES/patch-esES-Z.MPQ'})
        self.assertEqual(self.lock['launcher_profiles'], ['regular_client'])
        for package, entries in self.planned.items():
            if package.startswith('hd_client/'):
                for member in entries:
                    self.assertNotIn(member, ('dbfilesclient/creaturemodeldata.dbc', 'dbfilesclient/chrraces.dbc',
                                              'dbfilesclient/charsections.dbc'))
                    self.assertFalse(member.startswith(('character/', 'interface/', 'world/')))
        displays = c.rows(self.master('hd_client', 'CreatureDisplayInfo'), 'creaturedisplayinfo')
        self.assertFalse(set(range(91000, 91004)).intersection(displays))
        self.assertTrue(self.report['compatibility']['hd_client'].startswith('PRESERVED HISTORICAL HD CONTRACT'))
        self.assertFalse(self.report['feature_matrix']['hd_client']['full_feature_parity'])
        self.assertEqual(self.report['external_dependencies']['hd_client']['model_closure'],
                         'EXTERNAL BASELINE NOT AVAILABLE; NOT VERIFIED')
        self.assertFalse(any(s.startswith('native:character/') for s in self.sources.cache))
        self.assertEqual(self.report['runtime_rendering'], 'NOT RUN')

    def test_regular_delivery_unchanged(self):
        for path, digest in self.lock['preserved_regular_delivery'].items():
            self.assertEqual(c.file_sha(c.ROOT/'client_patches'/path), digest, path)

    def test_portals_physically_map_ordered(self):
        for profile in ('regular_client',):
            _, rows, _ = parse_dbc(self.master(profile, 'AreaTrigger'))
            self.assertEqual([r[1] for r in rows], sorted(r[1] for r in rows))
            self.assertEqual({r[0] for r in rows if r[0] in (900800, 900801)}, {900800, 900801})

    def test_readback_rejects_extra_member_and_bad_case_hash(self):
        # A real tiny MPQ exercises allowlisting, readback and case-insensitive lookup.
        lock = {'profiles': ['fixture'], 'launcher': self.lock['launcher']}
        package = 'fixture/Data/patch-Z.mpq'
        entry = {'name': 'Folder\\MiXeD.txt', 'data': b'original', 'category': 'fixture', 'provenance': []}
        planned = {package: {'folder/mixed.txt': entry}}
        with tempfile.TemporaryDirectory(prefix='consolidation-test-') as tmp:
            output = Path(tmp)/'delivery'
            c.build(output, planned, lock, {})
            c.verify(output, planned, lock)
            self.assertEqual(c.extract(output/package, 'folder\\mixed.txt'), b'original')
            disk = Path(tmp)/'extra'
            disk.write_bytes(b'not allowlisted')
            c.run('add', output/package, disk, 'unexpected.txt')
            with self.assertRaisesRegex(ValueError, 'Unexpected/missing MPQ members'):
                c.verify(output, planned, lock)

    def test_unsafe_names_rejected(self):
        for name in ('../member', '/absolute', 'x//y', 'x\\..\\y', 'x|y', 'C:/member'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                c.norm(name)


class SourceInputSafety(unittest.TestCase):
    def fixture(self, root):
        source = 'client_patches/old/Data/patch-Z.mpq'
        path = 'client_patches/archive/source-inputs/old/Data/patch-Z.mpq'
        disk = root/'payload'
        disk.write_bytes(b'pinned member')
        manifest = root/'manifest'
        manifest.write_text(str(disk)+'|Folder\\member.txt\n')
        archive = root/path
        archive.parent.mkdir(parents=True)
        c.run('create', archive, manifest)
        spec = {'path': path, 'sha256': c.file_sha(archive), 'members': {
            'folder/member.txt': {'name': 'Folder\\member.txt', 'sha256': c.sha(b'pinned member'),
                                 'size': len(b'pinned member')}}}
        return source, spec, {'sources': {source: spec}, 'relocations': {source: path}}

    def test_missing_archived_input_rejects_old_root_fallback(self):
        with tempfile.TemporaryDirectory(prefix='consolidation-source-') as tmp:
            root = Path(tmp)
            source, spec, lock = self.fixture(root)
            old = root/source
            old.parent.mkdir(parents=True)
            (root/spec['path']).rename(old)
            with patch.object(c, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'Missing source input:.*old/Data/patch-Z.*recover the pinned baseline'):
                    c.Sources(lock).get(source)
                with self.assertRaisesRegex(ValueError, 'Missing source input: launcher:'):
                    c.pinned_path('launcher', spec)

    def test_archive_corruption_rejected_before_member_read(self):
        with tempfile.TemporaryDirectory(prefix='consolidation-source-') as tmp:
            root = Path(tmp)
            source, spec, lock = self.fixture(root)
            with patch.object(c, 'ROOT', root):
                self.assertEqual(c.Sources(lock).get(source)['folder/member.txt'][1], b'pinned member')
                with (root/spec['path']).open('ab') as stream:
                    stream.write(b'corrupt archive bytes')
                with self.assertRaisesRegex(ValueError, 'Source archive changed:'), patch.object(c, 'extract') as extract:
                    c.Sources(lock).get(source)
                extract.assert_not_called()

    def test_member_hash_and_size_enforced_independently(self):
        with tempfile.TemporaryDirectory(prefix='consolidation-source-') as tmp:
            root = Path(tmp)
            source, spec, lock = self.fixture(root)
            entry = spec['members']['folder/member.txt']
            with patch.object(c, 'ROOT', root):
                for field, wrong in (('sha256', '0'*64), ('size', 1)):
                    with self.subTest(field=field), patch.dict(entry, {field: wrong}):
                        with self.assertRaisesRegex(ValueError, 'Source member changed:'):
                            c.Sources(lock).get(source)


class PublicationSafety(unittest.TestCase):
    def test_failed_swap_rolls_back_and_allows_retry(self):
        original_lock = json.loads(c.LOCK.read_text())
        lock = {'profiles': ['fixture'], 'launcher': original_lock['launcher'], 'relocations': {}}
        member = {'name': 'file.txt', 'data': b'previous', 'category': 'fixture', 'provenance': []}
        planned = {'fixture/Data/patch-Z.mpq': {'file.txt': member}}
        with tempfile.TemporaryDirectory(prefix='consolidation-publish-') as tmp:
            root = Path(tmp)
            destination, output = root/'client_patches', root/'build'
            c.build(destination, planned, lock, {})
            before = {str(p.relative_to(destination)): c.file_sha(p) for p in destination.rglob('*') if p.is_file()}
            member['data'] = b'replacement'
            c.build(output, planned, lock, {})
            rename = Path.rename

            def fail_last_swap(path, target):
                if path.name == 'checksums.json' and path.parent.name == 'new':
                    raise OSError('simulated swap failure')
                return rename(path, target)

            with patch.object(c, 'ROOT', root), patch.object(Path, 'rename', fail_last_swap):
                with self.assertRaisesRegex(OSError, 'simulated swap failure'):
                    c.publish(output, lock)
            self.assertEqual(before, {str(p.relative_to(destination)): c.file_sha(p)
                                      for p in destination.rglob('*') if p.is_file()})
            with patch.object(c, 'ROOT', root):
                c.publish(output, lock)
            self.assertEqual((destination/'checksums.json').read_bytes(), (output/'checksums.json').read_bytes())
            self.assertEqual(c.extract(destination/'fixture/Data/patch-Z.mpq', 'file.txt'), b'replacement')

    def test_archival_rerun_rejects_corrupted_retained_bytes(self):
        with tempfile.TemporaryDirectory(prefix='consolidation-archive-') as tmp:
            root = Path(tmp)
            for relative in c.ARCHIVE_DIRS:
                source = root/'client_patches'/relative
                source.mkdir(parents=True)
                (source/'content').write_bytes(b'original')
            with patch.object(c, 'ROOT', root):
                c.archive_optionals()
                c.archive_optionals()
                (root/'client_patches/archive'/c.ARCHIVE_DIRS[0]/'content').write_bytes(b'corrupt')
                with self.assertRaisesRegex(ValueError, 'Archived inventory/hash differs'):
                    c.archive_optionals()

    def test_archive_root_symlink_rejected(self):
        with tempfile.TemporaryDirectory(prefix='consolidation-symlink-') as tmp:
            root = Path(tmp)
            for relative in c.ARCHIVE_DIRS:
                source = root/'client_patches'/relative
                source.mkdir(parents=True)
                (source/'content').write_bytes(b'original')
            with patch.object(c, 'ROOT', root):
                c.archive_optionals()
                archived = root/'client_patches/archive'/c.ARCHIVE_DIRS[0]
                moved = root/'elsewhere'
                archived.rename(moved)
                archived.symlink_to(moved, target_is_directory=True)
                with self.assertRaisesRegex(ValueError, 'root is a symlink'):
                    c.archive_optionals()


if __name__ == '__main__':
    unittest.main()
