"""Durable installer contract fixtures; optional full-data test copies read-only DEV inputs."""
import sys
sys.dont_write_bytecode = True

import os
import shutil
import struct
from pathlib import Path

import apply_project_server_data as app
from build_high_elf_server_data import previous_owned
import test_apply_project_server_data as pilot
from crypt_release_dbc import parse_dbc

dbc, ROOT = pilot.dbc, pilot.ROOT


class HighElfInstallerTests(pilot.ServerDataTests):
    # Reuse the original pilot fixture, but do not duplicate its test methods.
    def write_manifest(self):
        document = dict(schema=1, files=self.files)
        if hasattr(self, 'contract'):
            document.update(schema=2, geography=self.contract)
        self.manifest.write_bytes(app.json_bytes(document))

    def geography(self):
        self.contract = dict(vmap_tiles=['vmaps/000_00_00.vmtile'],
                             model_closure=['vmaps/shared.vmo'], mmap_tiles=[], map_dependencies={})
        # ModelSpawn plus global node index, using the native filename contract.
        name = b'shared'
        spawn = bytes(38) + struct.pack('<I', len(name)) + name + bytes(4)
        tile = b'VMAP_4.8' + struct.pack('<I', 1) + spawn
        self.add_source(self.files, 'vmaps/000_00_00.vmtile', tile, 'copy')
        self.add_source(self.files, 'vmaps/000.vmtree', b'VMAP_4.8new-tree', 'replace')
        self.files['turtle-crypt/vmaps/000.vmtree']['accepted_before'] = [app.sha(b'VMAP_4.8')]
        params = struct.pack('<5f2I', 0, 0, 0, 100, 100, 100, 100)
        (self.target / 'mmaps/000.mmap').write_bytes(params)
        self.add_source(self.files, 'mmaps/000.mmap', params, 'copy')
        tile = bytearray(156)
        struct.pack_into('<4I', tile, 0, 0x4d4d4150, 7, 20, len(tile) - 56)
        struct.pack_into('<15I', tile, 56, 0x444e4156, 7, 0, 0, 0, 0, 1, *([0] * 8))
        (self.target / 'mmaps/0000000.mmtile').write_bytes(tile)
        self.write_manifest()

    def donor(self, name, ident, value=0, prefix='high-elf-map'):
        target = 'dbc/' + name
        fields, strings = app.ADDITIVE_DBC[target]
        row = [ident] + [0] * (fields - 1)
        row[-1] = value
        raw = dbc(fields, [row])
        path = self.source / prefix / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        self.files[prefix + '/' + target] = dict(path=target, size=len(raw),
                                                sha256=app.sha(raw), kind='additive-dbc')
        base = self.target / target
        if not base.exists():
            base.write_bytes(dbc(fields, [[1] + [0] * (fields - 1)]))
        self.write_manifest()

    def test_four_additive_deltas_ordered_donors_crypt_and_rollback(self):
        self.geography()
        for name in ('AreaTable.dbc', 'WMOAreaTable.dbc', 'WorldMapArea.dbc', 'WorldMapOverlay.dbc'):
            self.donor(name, 6000)
        self.donor('AreaTable.dbc', 6001, prefix='z-second')
        _, outputs = app.plan(self.manifest, self.target)
        rows = parse_dbc(outputs['dbc/AreaTable.dbc'])[1]
        self.assertEqual([r[0] for r in rows], [1, 6000, 5086, 6001])
        originals = {p: p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
        self.install()
        self.assertEqual(self.install()['status'], 'already-installed')
        self.rollback()
        self.assertEqual({p: p.read_bytes() for p in self.target.rglob('*') if p.is_file()}, originals)

    def test_conflicting_donor_rejected_before_writes(self):
        self.geography()
        self.donor('AreaTable.dbc', 6000)
        self.donor('AreaTable.dbc', 6000, 1, 'z-conflict')
        with self.assertRaisesRegex(ValueError, 'DBC ID collision'):
            app.inventory(self.manifest)
        with self.assertRaisesRegex(ValueError, 'DBC ID collision'):
            self.install()
        self.assertFalse(self.state.exists())

    def test_four_deltas_preserve_native_strings_and_reject_native_conflicts(self):
        self.geography()
        for target, (fields, strings) in app.ADDITIVE_DBC.items():
            with self.subTest(target=target):
                self.donor(Path(target).name, 6000)
                path = self.target / target
                row = [1] + [0] * (fields - 1)
                row[strings[0]] = 1
                block = b'\0native unrelated string\0'
                native = (struct.pack('<4s4I', b'WDBC', 1, fields, fields * 4, len(block)) +
                          struct.pack(f'<{fields}I', *row) + block)
                path.write_bytes(native)
                _, outputs = app.plan(self.manifest, self.target)
                merged = outputs[target]
                self.assertEqual(merged[20:20 + fields * 4], native[20:20 + fields * 4])
                self.assertTrue(parse_dbc(merged)[2].startswith(block))
                conflicting = [6000] + [0] * (fields - 1)
                conflicting[-1] = 999
                # Use the valid native string block for the original row.
                raw = dbc(fields, [row, conflicting])[:-1] + block
                raw = raw[:16] + struct.pack('<I', len(block)) + raw[20:]
                path.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, 'DBC ID collision'):
                    self.install()
                path.write_bytes(native)

    def test_guarded_binary_replace_unknown_and_reapply(self):
        self.geography()
        tree = self.target / 'vmaps/000.vmtree'
        tree.write_bytes(b'VMAP_4.8unknown')
        with self.assertRaisesRegex(ValueError, 'payload collision'):
            self.install()
        self.assertFalse(self.state.exists())
        tree.write_bytes(b'VMAP_4.8')
        self.install()
        self.assertEqual(self.install()['status'], 'already-installed')
        self.rollback()
        self.assertEqual(tree.read_bytes(), b'VMAP_4.8')

    def test_fullset_closure_stale_and_model_conflict(self):
        self.geography()
        self.contract['vmap_tiles'].append('vmaps/000_01_00.vmtile')
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'fullset'):
            app.inventory(self.manifest)
        self.contract['vmap_tiles'].pop()
        self.contract['model_closure'] = []
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'closure'):
            app.inventory(self.manifest)
        self.contract['model_closure'] = ['vmaps/shared.vmo']
        self.write_manifest()
        self.contract['mmap_tiles'] = ['mmaps/0000100.mmtile']
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'MMap fullset'):
            app.inventory(self.manifest)
        self.contract['mmap_tiles'] = []
        self.write_manifest()
        stale = self.target / 'vmaps/000_01_00.vmtile'
        stale.write_bytes(b'VMAP_4.8')
        with self.assertRaisesRegex(ValueError, 'Stale installed'):
            self.install()
        stale.unlink()
        (self.target / 'vmaps/shared.vmo').write_bytes(b'VMAP_4.8unknown')
        with self.assertRaisesRegex(ValueError, 'payload collision'):
            self.install()

    def test_previous_owned_model_replace_install_reapply_rollback(self):
        self.geography()
        model = self.target / 'vmaps/shared.vmo'
        previous = b'VMAP_4.8previous-owned-model'
        model.write_bytes(previous)
        record = self.files['turtle-crypt/vmaps/shared.vmo']
        record.update(kind='replace', accepted_before=[app.sha(previous)])
        self.write_manifest()
        model.write_bytes(b'VMAP_4.8unknown-native-model')
        with self.assertRaisesRegex(ValueError, 'payload collision'):
            self.install()
        self.assertFalse(self.state.exists())
        model.write_bytes(previous)
        self.install()
        self.assertEqual(model.read_bytes(), b'VMAP_4.8model')
        self.assertEqual(self.install()['status'], 'already-installed')
        self.rollback()
        self.assertEqual(model.read_bytes(), previous)

    def test_previous_ownership_requires_verified_high_elf_source(self):
        name = 'vmaps/He_195A0A632Bd23Cea9A73_Highelfhousevariantb.wmo.vmo'
        source = self.source / 'high-elf-map' / name
        source.parent.mkdir(parents=True)
        raw = b'VMAP_4.8previous-custom-model'
        source.write_bytes(raw)
        self.files['high-elf-map/' + name] = dict(path=name, kind='copy',
                                                 sha256=app.sha(raw), size=len(raw))
        self.write_manifest()
        self.assertEqual(set(previous_owned(self.manifest)), {name})
        source.write_bytes(b'VMAP_4.8drift')
        with self.assertRaisesRegex(ValueError, 'Source hash/size mismatch'):
            previous_owned(self.manifest)

    def test_mmap_params_halo_dependencies_and_capacity(self):
        self.geography()
        self.contract['map_dependencies'] = {'maps/0000000.map': [app.sha(b'wrong')]}
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'Halo dependency'):
            self.install()
        self.contract['map_dependencies']['maps/0000000.map'] = [app.file_sha(self.target / 'maps/0000000.map')]
        self.write_manifest()
        before, _ = app.plan(self.manifest, self.target)
        self.assertIn('maps/0000000.map', before['dependencies'])
        params = self.target / 'mmaps/000.mmap'
        params.write_bytes(struct.pack('<5f2I', 1, 0, 0, 100, 100, 100, 100))
        with self.assertRaisesRegex(ValueError, 'params compatibility'):
            self.install()
        params.write_bytes(struct.pack('<5f2I', 0, 0, 0, 100, 100, 100, 100))
        duplicate = self.target / 'mmaps/0000100.mmtile'
        duplicate.write_bytes((self.target / 'mmaps/0000000.mmtile').read_bytes())
        with self.assertRaisesRegex(ValueError, 'duplicate coordinate'):
            self.install()
        duplicate.unlink()
        tile = self.target / 'mmaps/0000000.mmtile'
        raw = bytearray(tile.read_bytes())
        struct.pack_into('<I', raw, 56 + 6 * 4, 101)
        tile.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'poly capacity'):
            self.install()

    def test_expected_plan_binds_unwritten_halo_dependencies(self):
        self.geography()
        terrain = self.target / 'maps/0000000.map'
        alternate = terrain.read_bytes() + b'another known encoding'
        self.contract['map_dependencies'] = {
            'maps/0000000.map': [app.file_sha(terrain), app.sha(alternate)]}
        self.write_manifest()
        before, _ = app.plan(self.manifest, self.target)
        expected = self.root / 'expected.json'
        expected.write_bytes(app.json_bytes(before))
        terrain.write_bytes(alternate)
        with self.assertRaisesRegex(ValueError, 'since pre-SQL'):
            self.install(expected_plan=expected)
        self.assertFalse(self.state.exists())

    def test_real_durable_fixture_install_reapply_rollback(self):
        if os.environ.get('HIGH_ELF_REAL_FIXTURE') != '1':
            self.skipTest('Set HIGH_ELF_REAL_FIXTURE=1 for read-only baseline copying')
        manifest = ROOT / 'data/server/manifest.json'
        _, payload = app.inventory(manifest)
        baseline = Path('/home/dev/azerothcore/env/dist/bin')
        target = self.root / 'real-target'
        names = set(payload) | set(payload.contract['map_dependencies'])
        for pattern in ('vmaps/000*.vmtile', 'mmaps/000*.mmtile', 'maps/000*.map'):
            names.update(p.relative_to(baseline).as_posix() for p in baseline.glob(pattern))
        for name in names:
            source = baseline / name
            if source.is_file():
                dest = target / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, dest)
        originals = {p.relative_to(target).as_posix(): app.file_sha(p)
                     for p in target.rglob('*') if p.is_file()}
        state = self.root / 'real-state'
        planned, _ = app.plan(manifest, target, state)
        expected = self.root / 'expected.json'
        expected.write_bytes(app.json_bytes(planned))
        self.assertEqual(app.install(manifest, target, state, True, expected)['status'], 'installed')
        self.assertEqual(app.install(manifest, target, state, True)['status'], 'already-installed')
        self.assertEqual(app.rollback(manifest, target, state, True)['status'], 'rolled-back')
        restored = {p.relative_to(target).as_posix(): app.file_sha(p)
                    for p in target.rglob('*') if p.is_file()}
        self.assertEqual(originals, restored)

    def test_real_stager_preserves_sources_and_exact_previous_guards(self):
        if os.environ.get('HIGH_ELF_REAL_FIXTURE') != '1':
            self.skipTest('Set HIGH_ELF_REAL_FIXTURE=1 for durable staging fixture')
        from stage_high_elf_server_data import stage
        build = ROOT / 'work/high-elf-server-wmo-dry-fixed'
        previous = ROOT / 'work/high-elf-server-before-wmo-dry-fixed'
        source = self.root / 'staging-fixture'
        shutil.copytree(previous, source)
        manifest = source / 'manifest.json'
        old_digest, _ = app.inventory(manifest)
        old = app.load_json(manifest.read_bytes())
        original_bytes = {n: (source / n).read_bytes() for n in old['files']}
        recovery = self.root / 'previous-sources'
        result = stage(build, manifest, recovery)
        self.assertEqual(app.inventory(recovery / 'manifest.json')[0], old_digest)
        self.assertEqual(app.inventory(manifest)[0],
                         app.inventory(ROOT / 'data/server/manifest.json')[0])
        new = app.load_json(manifest.read_bytes())
        changed_models = []
        for n, before in old['files'].items():
            after = new['files'][n]
            if after['sha256'] == before['sha256']:
                self.assertEqual((source / n).read_bytes(), original_bytes[n])
                self.assertEqual(after, before)
            elif after['kind'] == 'replace':
                self.assertEqual(set(after['accepted_before']),
                                 {before['sha256'], *before.get('accepted_before', [])})
                if Path(n).suffix in ('.vmo', '.m2'):
                    changed_models.append(n)
        report = app.load_json((build / 'report.json').read_bytes())
        expected_changes = {n for n, before in old['files'].items()
                            if not before['path'].startswith('dbc/') and
                            before['path'] in report['files'] and
                            report['files'][before['path']]['sha256'] != before['sha256']}
        self.assertEqual(set(result['changed_sources']), expected_changes)
        self.assertEqual(set(changed_models),
                         {n for n in expected_changes if Path(n).suffix in ('.vmo', '.m2')})
        # Even a contract-only change needs recovery before manifest mutation.
        dependency = next(iter(new['geography']['map_dependencies'].values()))
        dependency.append('0' * 64)
        manifest.write_bytes(app.json_bytes(new))
        alternate_build = self.root / 'contract-only-build'
        alternate_build.mkdir()
        for directory in ('geometry', 'server-dbc', 'navigation'):
            (alternate_build / directory).symlink_to(build / directory, target_is_directory=True)
        report['previous_manifest_sha256'] = app.file_sha(manifest)
        (alternate_build / 'report.json').write_bytes(app.json_bytes(report))
        shutil.copyfile(build / 'intended-files.json', alternate_build / 'intended-files.json')
        before_attempt = manifest.read_bytes()
        with self.assertRaisesRegex(ValueError, 'requires --recovery'):
            stage(alternate_build, manifest)
        self.assertEqual(manifest.read_bytes(), before_attempt)
        self.assertEqual({n: (source / n).read_bytes() for n in original_bytes}, original_bytes)


# The base suite is exercised in its own module, not inherited a second time.
for _name in list(vars(pilot.ServerDataTests)):
    if _name.startswith('test_') and _name not in vars(HighElfInstallerTests):
        setattr(HighElfInstallerTests, _name, None)
