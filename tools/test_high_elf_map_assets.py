#!/usr/bin/env python3
"""Binary contracts and read-only integration checks for the high-elf closure."""
import json
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from high_elf_map_assets import (ROOT, WMO_LIQUID_MANIFEST, Closure, Snapshot,
                                 adapt_wmo_dry_liquids, wmo_liquid_audit, active_textures, build_reader,
                                 client_path, digest, isolated, key, m2_textures,
                                 model_path, residual_layer_impact, rewrite_m2_textures,
                                 rewrite_tile, rewrite_wmo, run, strings, wmo_chunks)
from high_elf_terrain import Tile, chunk, u32
from test_high_elf_terrain import make_tile, placement


def wmo_root(motx=b'\0\0\0\0a.blp\0', modn=b'old.mdx\0', groups=0):
    header = bytearray(64)
    struct.pack_into('<I', header, 4, groups)
    material = bytearray(64)
    struct.pack_into('<I', material, 12, 4)
    # Secondary and tertiary textures deliberately point to different empty
    # padding positions. They must remain empty, not alias texture1.
    struct.pack_into('<I', material, 24, 2)
    doodad = bytearray(40)
    struct.pack_into('<I', doodad, 0, 0x9A000000)
    return b''.join(chunk(n[::-1].encode(), b) for n, b in (
        ('MVER', struct.pack('<I', 17)), ('MOHD', header),
        ('MOGI', bytes(32 * groups)), ('MOTX', motx), ('MOMT', material),
        ('MODN', modn), ('MODD', doodad)))


class FakeSnapshot:
    def __init__(self, resources):
        self.resources = {key(n): b for n, b in resources.items()}
        self.calls = []

    def get(self, name):
        self.calls.append(name)
        data = self.resources.get(key(name))
        return (data, {'sha256': digest(data), 'member': name}) if data is not None else None


def liquid_family(flags=5, liquid_type=15, group_flags=0, wet=False):
    root = bytearray(wmo_root(motx=b'', modn=b'', groups=2))
    # Remove dependent records so fixture tests exercise only family semantics.
    bodies = dict(wmo_chunks(root))
    bodies['MOMT'], bodies['MODD'] = b'', b''
    header = bytearray(bodies['MOHD'])
    struct.pack_into('<H', header, 60, flags)
    bodies['MOHD'] = bytes(header)
    root = b''.join(chunk(n[::-1].encode(), bodies[n]) for n, _ in wmo_chunks(root))
    mogp = bytearray(68)
    struct.pack_into('<I', mogp, 8, group_flags)
    struct.pack_into('<I', mogp, 52, liquid_type)
    raw = (chunk(b'REVM', struct.pack('<I', 17)) +
           chunk(b'PGOM', mogp + (chunk(b'QILM', bytes(64)) if wet else b'')))
    groups = [('World\\Test_000.wmo', raw), ('World\\Test_001.wmo', raw)]
    policy = {'source': 'World\\Test.wmo', 'sha256': digest(root), 'root_flags': flags,
              'groups': [{'source': n, 'sha256': digest(b)} for n, b in groups]}
    return root, groups, policy


class DryWMOLiquidContracts(unittest.TestCase):
    def test_only_mohd_bit_changes_and_post_audit_is_dry(self):
        for flags in (4, 5):
            root, groups, policy = liquid_family(flags=flags)
            out, audit = adapt_wmo_dry_liquids(root, policy['source'], groups, policy)
            self.assertFalse(audit['before']['all_dry'])
            self.assertTrue(all(r['legacy_15_to_19_bbox_magma'] for r in audit['before']['groups']))
            self.assertTrue(audit['after']['all_dry'])
            expected = bytearray(root)
            expected[root.index(b'DHOM') + 8 + 60] &= ~4
            self.assertEqual(out, bytes(expected))

    def test_wet_non15_or_liquid_flag_refused_even_with_matching_hashes(self):
        for kwargs in ({'wet': True}, {'liquid_type': 1}, {'group_flags': 0x1000}):
            with self.subTest(kwargs=kwargs):
                root, groups, policy = liquid_family(**kwargs)
                with self.assertRaisesRegex(ValueError, 'non-sentinel/wet'):
                    adapt_wmo_dry_liquids(root, policy['source'], groups, policy)

    def test_identity_hash_and_complete_family_guards(self):
        root, groups, policy = liquid_family()
        for source, data, payloads in (
                ('World\\Other.wmo', root, groups),
                (policy['source'], root + chunk(b'GOFM', b'changed'), groups),
                (policy['source'], root, groups[:1]),
                (policy['source'], root, [groups[0], ('World\\Other_001.wmo', groups[1][1])]),
                (policy['source'], root, [groups[0], (groups[1][0], groups[1][1] + chunk(b'GOFM', b'changed'))])):
            with self.subTest(source=source, size=len(data), groups=payloads), self.assertRaises(ValueError):
                adapt_wmo_dry_liquids(data, source, payloads, policy)

    def test_native_active_volumes_and_unknown_custom_family_are_untouched(self):
        # Both a native no-grid sentinel and a real active native grid bypass
        # the source-only policy, even when identity/hash exactly match it.
        for kwargs in ({'flags': 1}, {'flags': 5, 'liquid_type': 1,
                                     'group_flags': 0x1000, 'wet': True}):
            root, groups, policy = liquid_family(**kwargs)
            with tempfile.TemporaryDirectory() as td:
                payloads = dict(groups, **{policy['source']: root})
                native = FakeSnapshot(payloads)
                closure = Closure(native, FakeSnapshot({}), Path(td), None, Path(td),
                                  {'families': [policy]})
                closure.resolve(policy['source'], 'wmo')
                self.assertFalse(closure.blockers)
                self.assertFalse(closure.files)
                entry = next(iter(closure.resources.values()))
                self.assertNotIn('liquid_adaptation', entry)
                self.assertEqual(native.resources[key(policy['source'])], root)
        root, groups, policy = liquid_family()
        with tempfile.TemporaryDirectory() as td:
            closure = Closure(FakeSnapshot({}), FakeSnapshot(dict(groups, **{policy['source']: root})),
                              Path(td), None, Path(td), {'families': []})
            target = closure.resolve(policy['source'], 'wmo')
            self.assertFalse(closure.blockers)
            emitted = (Path(td) / 'files' / target.replace('\\', '/')).read_bytes()
            self.assertEqual(dict(wmo_chunks(emitted))['MOHD'], dict(wmo_chunks(root))['MOHD'])

    def test_last_group_failure_emits_no_family_files(self):
        root, groups, policy = liquid_family()
        _, wet_groups, _ = liquid_family(wet=True)
        payloads = {policy['source']: root, groups[0][0]: groups[0][1], groups[1][0]: wet_groups[1][1]}
        with tempfile.TemporaryDirectory() as td:
            closure = Closure(FakeSnapshot({}), FakeSnapshot(payloads), Path(td), None, Path(td),
                              {'families': [policy]})
            closure.resolve(policy['source'], 'wmo')
            self.assertIn('non-sentinel/wet', closure.blockers[0]['reason'])
            self.assertFalse(closure.files)

    @unittest.skipUnless((ROOT / 'work/high-elf-assets-mclq-fixed-v2/manifest.json').is_file(),
                         'locked source evidence required')
    def test_all_15_locked_real_families_and_provenance(self):
        manifest = json.loads(WMO_LIQUID_MANIFEST.read_text())
        evidence = manifest['evidence']
        for name in ('assets_manifest', 'archived_assets_manifest'):
            self.assertEqual(digest((ROOT / evidence[name]).read_bytes()), evidence['assets_manifest_sha256'])
        self.assertEqual(len(manifest['families']), 15)
        baseline = json.loads((ROOT / evidence['assets_manifest']).read_text())
        entries = {key(r['source']): r for r in baseline['resources'] if r['kind'] == 'wmo'}
        count = 0
        for policy in manifest['families']:
            def read(record):
                return (ROOT / evidence['source_payload_directory'] /
                        (digest(key(record['source']).encode()) + '.bin')).read_bytes()
            entry = entries[key(policy['source'])]
            self.assertEqual(entry['provenance']['sha256'], policy['sha256'])
            groups = [(g['source'], read(g)) for g in policy['groups']]
            self.assertEqual([g['sha256'] for g in policy['groups']],
                             [g['provenance']['sha256'] for g in entry['groups']])
            root = read(policy)
            out, audit = adapt_wmo_dry_liquids(root, policy['source'], groups, policy)
            self.assertTrue(audit['after']['all_dry'])
            before, after = dict(wmo_chunks(root)), dict(wmo_chunks(out))
            expected = bytearray(before.pop('MOHD'))
            expected[60] &= ~4
            self.assertEqual(after.pop('MOHD'), expected)
            self.assertEqual(before, after)
            count += len(groups)
        self.assertEqual(count, 27)

    @unittest.skipUnless((ROOT / 'work/high-elf-assets-wmo-dry-fixed/manifest.json').is_file(),
                         'final dry candidate required')
    def test_final_closure_changes_exactly_15_root_fields(self):
        old = ROOT / 'work/high-elf-assets-mclq-fixed-v2'
        new = ROOT / 'work/high-elf-assets-wmo-dry-fixed'
        before = json.loads((old / 'manifest.json').read_text())
        after = json.loads((new / 'manifest.json').read_text())
        self.assertTrue(after['asset_closure_complete'])
        self.assertFalse(after['blockers'])
        old_files = {r['path']: r for r in before['files']}
        new_files = {r['path']: r for r in after['files']}
        self.assertEqual(old_files.keys(), new_files.keys())
        adapted = {r['target']: r for r in after['resources'] if 'liquid_adaptation' in r}
        self.assertEqual(len(adapted), 15)
        changed = []
        for path in old_files:
            a = (old / 'files' / path.replace('\\', '/')).read_bytes()
            b = (new / 'files' / path.replace('\\', '/')).read_bytes()
            self.assertEqual(digest(b), new_files[path]['sha256'])
            if a != b:
                changed.append(path)
                self.assertIn(path, adapted)
                expected = bytearray(a)
                offset = a.index(b'DHOM') + 8 + 60
                expected[offset] &= ~4
                self.assertEqual(b, bytes(expected), path)
                self.assertTrue(adapted[path]['liquid_adaptation']['staged_audit']['all_dry'])
        self.assertEqual(set(changed), set(adapted))
        custom = [r for r in after['resources'] if r['kind'] == 'wmo' and r['status'] == 'staged']
        self.assertEqual(len(custom), 20)
        self.assertEqual(sum(len(r['groups']) for r in custom), 43)
        for r in custom:
            root = (new / 'files' / r['target'].replace('\\', '/')).read_bytes()
            groups = [(g['source'], (new / 'files' /
                       (r['target'][:-4] + f'_{i:03}.wmo').replace('\\', '/')).read_bytes())
                      for i, g in enumerate(r['groups'])]
            self.assertTrue(wmo_liquid_audit(root, groups)['all_dry'])


class BinaryContracts(unittest.TestCase):
    def test_isolation_paths_and_vmap_flattening(self):
        a, b = isolated('World\\A\\House.wmo'), isolated('World\\B\\House.wmo')
        self.assertNotEqual(a.rsplit('\\', 1)[-1], b.rsplit('\\', 1)[-1])
        self.assertEqual(a, isolated('world/a/house.WMO'))
        self.assertEqual(model_path('World\\Model.MDL'), 'World\\Model.m2')
        self.assertEqual(client_path('World\\Weapons&Armor\\x.mdx'), 'World\\Weapons&Armor\\x.mdx')
        for bad in ('../outside.m2', '/absolute', 'a\\..\\b', 'a\nb', 'C:\\x', 'a\\\\b'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                isolated(bad)

    def test_wmo_offsets_empty_sentinels_and_doodad_flags(self):
        source = wmo_root()
        target, deps = rewrite_wmo(source, lambda n, k: 'Custom\\long_' + n.replace('.mdx', '.m2'))
        old, new = dict(wmo_chunks(source)), dict(wmo_chunks(target))
        texture = u32(new['MOMT'], 12)
        self.assertEqual(strings(new['MOTX'])[texture], 'Custom\\long_a.blp')
        for field in (24, 36):
            self.assertEqual(new['MOTX'][u32(new['MOMT'], field)], 0)
        self.assertEqual(u32(new['MODD'], 0) & 0xff000000, 0x9A000000)
        self.assertEqual(strings(new['MODN'])[u32(new['MODD'], 0) & 0xffffff], 'Custom\\long_old.mdx')
        self.assertEqual(old['MODD'][4:], new['MODD'][4:])
        self.assertEqual(old['MOHD'], new['MOHD'])
        self.assertEqual(len(deps), 2)

    def test_invalid_wmo_offsets_fail(self):
        source = bytearray(wmo_root())
        p = source.index(b'TMOM') + 8
        struct.pack_into('<I', source, p + 12, 5)  # middle of a.blp
        with self.assertRaisesRegex(ValueError, 'outside MOTX'):
            rewrite_wmo(source, lambda n, k: n)

    def test_inactive_legacy_material_scalar_is_not_treated_as_texture(self):
        source = bytearray(wmo_root())
        p = source.index(b'TMOM') + 8
        struct.pack_into('<f', source, p + 36, 0.1)
        adaptations = []
        rewritten, _ = rewrite_wmo(source, lambda n, k: n, adaptations)
        self.assertEqual(u32(dict(wmo_chunks(rewritten))['MOMT'], 36), 0)
        self.assertEqual(adaptations[0]['field'], 36)
        # A required second texture for Env shader must never be discarded.
        struct.pack_into('<I', source, p + 4, 3)
        struct.pack_into('<f', source, p + 24, 0.1)
        with self.assertRaisesRegex(ValueError, 'outside MOTX'):
            rewrite_wmo(source, lambda n, k: n)

    def test_m2_string_append_preserves_geometry_and_texture_flags(self):
        for version, field in ((256, 92), (264, 80)):
            with self.subTest(version=version):
                source = bytearray(400)
                source[:4] = b'MD20'
                struct.pack_into('<I', source, 4, version)
                struct.pack_into('<2I', source, field, 1, 324)
                struct.pack_into('<4I', source, 324, 0, 0x123, 6, 350)
                source[350:356] = b'a.blp\0'
                target = rewrite_m2_textures(source, {key('a.blp'): 'Native\\long.blp'})
                self.assertEqual(m2_textures(target), [(324, 'Native\\long.blp')])
                self.assertEqual(target[:332], source[:332])
                self.assertEqual(target[340:400], source[340:400])

    def test_adt_mmid_mwid_relayout_preserves_slots_cells_and_uids(self):
        source = make_tile(models=[placement(11, 0, 0), placement(12, 0, 0, name=1)],
                           wmos=[placement(21, 0, 0, 64)],
                           refs={0: ([0, 1], [0])}, model_names=(b'a.mdx', b'b.mdx'),
                           model_ids=struct.pack('<2I', 0, 6))
        before = Tile(source)
        # Explicit reordered/repeated MMID slots, independent of string order.
        raw = bytearray(source)
        pos = before.offsets['mmid'] + 8
        struct.pack_into('<2I', raw, pos, 6, 0)
        before = Tile(bytes(raw))
        calls = []

        def mapper(name, kind):
            calls.append((name, kind))
            return 'Longer\\custom_' + name

        after = Tile(rewrite_tile(bytes(raw), mapper))
        self.assertEqual(after.cells, before.cells)
        self.assertEqual(after.refs, before.refs)
        for k in range(2):
            self.assertEqual([r[4:] for _, r in before.placements[k]],
                             [r[4:] for _, r in after.placements[k]])
            self.assertEqual([b'Longer\\custom_' + n for n, _ in before.placements[k]],
                             [n for n, _ in after.placements[k]])

    def test_missing_models_never_resolve_by_similarity(self):
        with tempfile.TemporaryDirectory() as td:
            native = FakeSnapshot({'World\\Similar.m2': b'not the requested model'})
            closure = Closure(native, FakeSnapshot({}), Path(td), None, Path(td) / 'missing.dll')
            self.assertEqual(closure.resolve('World\\Intended.m2', 'm2'), 'World\\Intended.m2')
            self.assertEqual(len(closure.blockers), 1)
            self.assertFalse(closure.files)

    def test_native_group_hole_never_filled_from_source(self):
        with tempfile.TemporaryDirectory() as td:
            native = FakeSnapshot({'World\\House.wmo': wmo_root(groups=1)})
            source = FakeSnapshot({'World\\House_000.wmo': b'source group'})
            closure = Closure(native, source, Path(td), None, Path(td) / 'converter')
            closure.resolve('World\\House.wmo', 'wmo')
            self.assertIn('Missing WMO group', closure.blockers[0]['reason'])
            self.assertFalse(source.calls)
            self.assertFalse(closure.files)

    def test_failed_dependency_propagates(self):
        with tempfile.TemporaryDirectory() as td:
            closure = Closure(FakeSnapshot({}), FakeSnapshot({}), Path(td), None, Path(td))
            closure.resources = {'parent': {'status': 'staged'}, 'child': {'status': 'blocked'}}
            closure.edges = [{'parent': 'parent', 'resource_id': 'child'}]
            closure.finalize()
            self.assertEqual(closure.resources['parent']['status'], 'incomplete')
            self.assertEqual(closure.resources['parent']['unresolved_dependency_ids'], ['child'])

    def test_native_embedded_flag_and_missing_appearance_binding(self):
        with tempfile.TemporaryDirectory() as td:
            model = bytearray(500)
            model[:4] = b'MD20'
            struct.pack_into('<I', model, 4, 264)
            struct.pack_into('<2I', model, 28, 1, 320)
            struct.pack_into('<I', model, 332, 0x100)
            native = FakeSnapshot({'World\\test.m2': model})
            closure = Closure(native, FakeSnapshot({}), Path(td), None, Path(td))
            closure.resolve('World\\test.m2', 'm2')
            self.assertFalse(closure.blockers)
            self.assertFalse(any(n.endswith('.anim') for n in native.calls))
            struct.pack_into('<2I', model, 80, 1, 400)
            struct.pack_into('<4I', model, 400, 1, 0, 0, 0)
            closure = Closure(FakeSnapshot({'World\\test.m2': model}), FakeSnapshot({}), Path(td), None, Path(td))
            closure.resolve('World\\test.m2', 'm2')
            self.assertIn('replaceable texture bindings', closure.blockers[0]['reason'])

    def test_native_skin_invalid_payload_is_a_failed_dependency(self):
        with tempfile.TemporaryDirectory() as td:
            model = bytearray(304)
            model[:4] = b'MD20'
            struct.pack_into('<I', model, 4, 264)
            struct.pack_into('<I', model, 68, 1)
            native = FakeSnapshot({'World\\test.m2': model, 'World\\test00.skin': b'invalid'})
            closure = Closure(native, FakeSnapshot({}), Path(td), None, Path(td))
            closure.resolve('World\\test.m2', 'm2')
            closure.finalize()
            self.assertEqual(closure.resources['prefer-native:world\\test.m2']['status'], 'incomplete')
            self.assertIn('SKIN', closure.blockers[0]['reason'])

    def test_converter_semantic_failure_marks_emitted_model_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            (out / 'evidence').mkdir()
            converter = out / 'converter.dll'
            converter.touch()
            source = bytearray(324)
            source[:4] = b'MD20'
            struct.pack_into('<I', source, 4, 256)

            def conversion(args):
                output = Path(args[args.index('--output') + 1])
                model = bytearray(304)
                model[:4] = b'MD20'
                struct.pack_into('<I', model, 4, 264)
                output.write_bytes(model)
                Path(str(output) + '.report.json').write_text(json.dumps({
                    'fullySupported': False, 'unsupportedSemantics': ['unresolved'],
                    'hardcodedResources': [], 'skins': 0}))
                return SimpleNamespace(returncode=0, stdout='', stderr='')

            closure = Closure(FakeSnapshot({}), FakeSnapshot({'World\\test.m2': source}), out, 'dotnet', converter)
            with patch('high_elf_map_assets.run', conversion):
                closure.resolve('World\\test.m2', 'm2')
            self.assertTrue(closure.files)
            self.assertEqual(closure.resources['prefer-native:world\\test.m2']['status'], 'blocked')


@unittest.skipUnless((ROOT / 'tools/mpq').is_file() and
                     (ROOT / 'tools/stormlib/lib/libstorm.a').is_file(), 'local StormLib required')
class DirectMPQContracts(unittest.TestCase):
    def test_unlisted_higher_priority_payload_is_not_shadowed_by_cached_index(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data, evidence = root / 'Data', root / 'evidence'
            data.mkdir()
            evidence.mkdir()
            for archive, payload in (('common.MPQ', b'lower payload'), ('patch-2.MPQ', b'effective payload')):
                disk = root / 'input'
                disk.write_bytes(payload)
                listing = root / 'members.txt'
                listing.write_text(str(disk) + '|World\\x.blp\n')
                result = run([ROOT / 'tools/mpq', 'create', data / archive, listing])
                self.assertEqual(result.returncode, 0, result.stderr)
            reader = build_reader(evidence)
            snapshot = Snapshot(root, '335', evidence, ROOT / 'tools/mpq', reader=reader)
            try:
                snapshot.index.clear()  # Simulate incomplete listfiles in both archives.
                payload, provenance = snapshot.get('World\\x.blp')
                self.assertEqual(payload, b'effective payload')
                self.assertTrue(provenance['archive'].endswith('patch-2.MPQ'))
                self.assertIsNone(snapshot.get('World\\missing.blp'))
            finally:
                snapshot.close()


@unittest.skipUnless((ROOT / 'work/high-elf-terrain-candidate/Azeroth_35_25.adt').is_file(),
                     'local terrain candidates required')
class RealInputContracts(unittest.TestCase):
    def test_error_layer_impact_is_measured_and_never_implicitly_removed(self):
        path = ROOT / 'work/high-elf-terrain-candidate/Azeroth_35_25.adt'
        data = path.read_bytes()
        tile = Tile(data)
        impact = residual_layer_impact(tile, 85, 2)
        self.assertEqual(impact['histogram_4bit'], {0: 4094, 1: 1, 2: 1})
        self.assertEqual(len(impact['nonzero_samples']), 2)
        self.assertAlmostEqual(impact['mean_effective_weight'], 0.000048828125)
        self.assertEqual(impact['max_alpha_8bit'], 34)
        self.assertFalse(impact['applied'])
        self.assertEqual(tile.data, data)

    def test_candidate_hashes_and_terrain_preservation(self):
        root = ROOT / 'work/high-elf-assets-candidate'
        if not (root / 'manifest.json').is_file():
            self.skipTest('run the asset builder first')
        manifest = json.loads((root / 'manifest.json').read_text())
        self.assertFalse(manifest['apply_ready'])
        self.assertEqual(len(manifest['tiles']), 24)
        for record in manifest['files']:
            raw = (root / 'files' / record['path'].replace('\\', '/')).read_bytes()
            self.assertEqual(digest(raw), record['sha256'], record['path'])
        for record in manifest['tiles']:
            before = Tile(Path(record['source']['path']).read_bytes())
            after = Tile((root / 'files' / record['target'].replace('\\', '/')).read_bytes())
            self.assertEqual(before.cells, after.cells)
            for k in range(2):
                self.assertEqual([raw[4:] for _, raw in before.placements[k]],
                                 [raw[4:] for _, raw in after.placements[k]])
        custom_wmos = [r for r in manifest['resources'] if r['kind'] == 'wmo'
                       and r['target'].startswith('Character\\Custom\\')]
        self.assertTrue(custom_wmos)
        for entry in custom_wmos:
            if entry['status'] == 'blocked':
                continue
            path = root / 'files' / entry['target'].replace('\\', '/')
            bodies = dict(wmo_chunks(path.read_bytes()))
            self.assertEqual(u32(bodies['MOHD'], 4), len(entry['groups']))
            for i, group in enumerate(entry['groups']):
                output = path.with_name(path.stem + f'_{i:03}.wmo')
                self.assertEqual(digest(output.read_bytes()), group['provenance']['sha256'])
        basenames = [r['path'].rsplit('\\', 1)[-1].lower() for r in manifest['files']
                     if r['path'].lower().endswith(('.wmo', '.m2'))]
        self.assertEqual(len(basenames), len(set(basenames)))


if __name__ == '__main__':
    unittest.main()
