#!/usr/bin/env python3
"""Binary invariants and optional original-source, two-build integration checks.

 python3 tools/test_new_races_assets.py
  DOTNET=/path/to/dotnet python3 tools/test_new_races_assets.py --integration work/FRESH
  python3 tools/test_new_races_assets.py --integration work/RETAINED --verify-existing \
    --previous-publication work/RETAINED/pass1/replaced-publication

Integration builds twice, independently reads delivered MPQs, compares native
row bytes/string prefixes and resource hashes, then requires identical MPQ hashes.
It does not launch a renderer or write client/server installations.
After publication, comparison requires a retained known-prior backup. An explicit
--previous-publication is preferred; otherwise try the live prior delivery, then
the output's pass1/replaced-publication. All four prior hashes must match before
reading retained reports or creating any fresh build output.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import build_new_races_assets as assets
from high_elf_eye_selectors import fix_selectors


def dbc(fields, size, rows, strings=b'\0'):
    return struct.pack('<4s4I', b'WDBC', len(rows), fields, size, len(strings))+b''.join(rows)+strings


def hair_proof_fixture(change=None):
    source = assets.DBC(dbc(10, 40, []), 10, 40)
    native = assets.DBC(dbc(10, 40, []), 10, 40)
    src_rows, nat_rows = [], []
    for style in range(20):
        for color in range(16):
            refs = [rf'Character\BloodElf\Hair00_{color:02}.blp',
                    rf'Character\BloodElf\ScalpLowerHair00_{min(color,10):02}.blp',
                    rf'Character\BloodElf\ScalpUpperHair00_{min(color,10):02}.blp']
            if change == 'fallback' and (style, color) == (0, 11):
                refs[1] = r'Character\BloodElf\ScalpLowerHair00_11.blp'
            src_rows.append([len(src_rows), 10, 1, 3, style, color, *[source.string(n) for n in refs], 0])
            if color <= 10:
                nat_rows.append([len(nat_rows), 10, 1, 3, *[native.string(n) for n in refs], 17, style, color])
    missing = set()
    for color in range(11):
        missing.update(rf'character\bloodelf\scalp{part}hair00_{color:02}.blp' for part in ('lower', 'upper'))
    for color in range(10):
        refs = [rf'Character\BloodElf\Facial{part}Hair00_{color:02}.blp' for part in ('Lower', 'Upper')]
        missing.update(n.lower() for n in refs)
        nat_rows.append([len(nat_rows), 10, 0, 2, *[native.string(n) for n in refs], 0, 17, 0, color])
    nat_rows += [[i]+[0]*9 for i in range(len(nat_rows), 8958)]
    source.append(src_rows[:-1] if change == 'combination' else src_rows)
    native.append(nat_rows)
    src_geo = [[s, 10, 1, s, s+2, 1 if change == 'show_scalp' and s == 0 else 0] for s in range(20)]
    nat_geo = [[s, 10, 1, s, s+2, 0] for s in range(20)]
    blobs = {'source:CharSections': source.encode(), 'validation:NativeCharSections': native.encode(),
             'source:CharHairGeosets': dbc(6, 24, [struct.pack('<6I', *r) for r in src_geo]),
             'native:CharHairGeosets': dbc(6, 24, [struct.pack('<6I', *r) for r in nat_geo])}
    return SimpleNamespace(m={'missing': missing, 'native_legacy_probe_archives': ['native.mpq']},
                           get=lambda key: blobs[key] if key in blobs else b'\1\2\3\4' if key.startswith('texture:') else b'\1\2\3\5',
                           archive=lambda name: name)


class PackedContracts(unittest.TestCase):
    def test_prior_backup_after_publication_and_fail_before_build_writes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); output = root/'work/fresh'
            backup = root/'retained-prior'
            relatives = [f'{e}/{r}' for e in ('primary', 'optional-extra-skins')
                         for r in ('Data/patch-Z.mpq', 'Data/esES/patch-esES-Z.MPQ')]
            expected = {}
            for i, name in enumerate(relatives):
                old = b'old'+bytes([i])
                expected[name] = assets.sha(old)
                for directory, raw in ((backup, old), (root/'client_patches/new-races', b'new')):
                    path = (root/'client_patches/archive/new-races'/name
                            if directory == root/'client_patches/new-races' and name.startswith('optional-extra-skins/')
                            else directory/name)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(raw)
            manifest = {'previous_publication': expected}
            manifest_path = root/'manifest.json'
            manifest_path.write_text(json.dumps(manifest))
            with patch.object(assets, 'ROOT', root), patch.object(assets, 'MANIFEST', manifest_path):
                self.assertEqual(previous_publication_root(output, manifest, backup), backup)
                with self.assertRaisesRegex(ValueError, 'all four exact known prior'):
                    previous_publication_root(output, manifest)
                # Default fallback works only when the entire pinned prior set matches.
                fallback = output/'pass1/replaced-publication'
                import shutil
                shutil.copytree(backup, fallback)
                self.assertEqual(previous_publication_root(output, manifest), fallback)
                # An explicit bad path must fail, even with a valid fallback available.
                with self.assertRaisesRegex(ValueError, 'all four exact known prior'):
                    previous_publication_root(output, manifest, root/'client_patches/new-races')
                (backup/relatives[-1]).write_bytes(b'wrong fourth archive')
                fresh = root/'work/never-created'
                with patch.object(assets, 'build') as build:
                    for verify_existing in (False, True):
                        with self.assertRaisesRegex(ValueError, relatives[-1]):
                            integration(fresh, verify_existing, backup)
                    build.assert_not_called()
                self.assertFalse(fresh.exists())
                # The live prior set is split across active primary and archive optional.
                for name, digest in expected.items():
                    assets.publication_path(name).write_bytes(b'old'+bytes([relatives.index(name)]))
                self.assertEqual(previous_publication_root(output, manifest), root/'client_patches/new-races')
                for name in relatives:
                    self.assertEqual(assets.file_sha(prior_archive(root/'client_patches/new-races', name)), expected[name])

    def test_publication_preflight_checksums_and_rollback(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); output = root/'build'; dest = root/'client_patches/new-races'
            output.mkdir(); dest.mkdir(parents=True)
            archives = {f'{e}/{r}': assets.sha(b'new') for e in ('primary', 'optional-extra-skins')
                        for r in ('Data/patch-Z.mpq', 'Data/esES/patch-esES-Z.MPQ')}
            for name in archives:
                p = output/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'new')
            report = {'editions': {e: {'archives': {r: {'sha256': assets.sha(b'new')}
                      for r in ('Data/patch-Z.mpq', 'Data/esES/patch-esES-Z.MPQ')}}
                      for e in ('primary', 'optional-extra-skins')}}
            assets.dump(output/'report.json', report)
            evidence = output/'validation.json'
            assets.dump(evidence, {'status': 'PASS', 'source_builds': 2, 'archives': archives})
            # Ancestor symlink and checksum symlink are rejected before any write.
            outside = root/'outside'; outside.mkdir()
            (dest/'primary').symlink_to(outside, target_is_directory=True)
            with patch.object(assets, 'ROOT', root), self.assertRaisesRegex(ValueError, 'escapes|Symlink'):
                assets.publish_output(output, evidence)
            (dest/'primary').unlink()
            (dest/'assets-SHA256SUMS').symlink_to(outside/'sums')
            with patch.object(assets, 'ROOT', root), self.assertRaisesRegex(ValueError, 'escapes|Symlink'):
                assets.publish_output(output, evidence)
            (dest/'assets-SHA256SUMS').unlink()
            real_replace = assets.os.replace
            calls = []
            def fail_fourth(src, dst):
                calls.append(dst)
                if len(calls) == 4:
                    raise OSError('injected replacement failure')
                real_replace(src, dst)
            with patch.object(assets, 'ROOT', root), patch.object(assets.os, 'replace', side_effect=fail_fourth):
                with self.assertRaisesRegex(OSError, 'injected'):
                    assets.publish_output(output, evidence)
            self.assertFalse(any(p.is_file() for p in dest.rglob('*')))
            self.assertFalse((root/'client_patches/archive/new-races').exists())
            # Input checksums are ignored; publisher computes hashes from staged bytes.
            (output/'SHA256SUMS').write_text('stale')
            with patch.object(assets, 'ROOT', root):
                assets.publish_output(output, evidence)
            sums = dict((line.split('  ')[1], line.split('  ')[0])
                        for line in (dest/'assets-SHA256SUMS').read_text().splitlines())
            with patch.object(assets, 'ROOT', root):
                self.assertTrue(all(assets.file_sha(assets.publication_path(n)) == digest for n, digest in sums.items()))
            self.assertFalse((dest/'optional-extra-skins').exists())
            manifest_path = root/'manifest.json'
            assets.dump(manifest_path, {'previous_publication': sums})
            with patch.object(assets, 'ROOT', root), patch.object(assets, 'MANIFEST', manifest_path):
                assets.publish_output(output, evidence, replace_known=True)
            for name, digest in sums.items():
                self.assertEqual(assets.file_sha(output/'replaced-publication'/name), digest)
            self.assertFalse((dest/'optional-extra-skins').exists())

    def test_role_validator_rejects_cpu_dxt_but_allows_direct_hair_and_extra(self):
        table = assets.DBC(dbc(10, 40, []), 10, 40)
        names = ['Character/Custom/TurtleHighElf/Male/'+s+'.blp' for s in ('body', 'extra', 'hair')]
        offsets = [table.string(n) for n in names]
        table.append([[22000, 22, 0, 0, offsets[0], offsets[1], 0, 17, 0, 0],
                      [22001, 22, 0, 3, offsets[2], 0, 0, 17, 0, 0]])
        header = struct.pack('<4sI4B2I', b'BLP2', 1, 2, 0, 0, 0, 4, 4)
        dxt = header+struct.pack('<16I', 148, *([0]*15))+struct.pack('<16I', 8, *([0]*15))+bytes(8)
        palette = bytearray(dxt[:148]+bytes(1024)+bytes(16))
        palette[8] = 1
        struct.pack_into('<I', palette, 20, 1172)
        struct.pack_into('<I', palette, 84, 16)
        payload = {'DBFilesClient/CharSections.dbc': table.encode(),
                   names[0]: bytes(palette), names[1]: dxt, names[2]: dxt}
        self.assertEqual(assets.validate_compositor(payload)['textures'], 1)
        payload[names[0]] = dxt
        with self.assertRaisesRegex(ValueError, 'CPU compositor requires palette'):
            assets.validate_compositor(payload)

    def test_class_pairs_are_bytes_and_preserve_original(self):
        raw = dbc(2, 2, [b'\x02\x08', b'\x08\x09'])
        table = assets.DBC(raw, 2, 2)
        table.append([[22, 1], [23, 9]], key=tuple)
        out = table.encode()
        self.assertEqual(out[20:24], raw[20:24])
        self.assertEqual(len(out), 29)
        self.assertEqual(assets.DBC(out, 2, 2).values(), [[2, 8], [8, 9], [22, 1], [23, 9]])
        with self.assertRaisesRegex(ValueError, 'collision'):
            table.append([[22, 1]], key=tuple)
        with self.assertRaisesRegex(ValueError, 'packed schema'):
            assets.DBC(dbc(2, 8, [struct.pack('<II', 22, 1)]), 2, 2)

    def test_outfit_packing_signed_sentinels_and_collision(self):
        values = [9002, 2, 8, 0, 0]+[-1]*72
        row = struct.pack('<I4B72i', *values)
        self.assertEqual(len(row), 296)
        table = assets.DBC(dbc(77, 296, [row], b'\0native\0'), 77, 296)
        self.assertEqual(table.values()[0], values)
        new = values.copy(); new[:2] = [90000, 23]
        table.append([new])
        with self.assertRaisesRegex(ValueError, 'collision'):
            table.append([new])
        self.assertEqual(table.encode()[20:316], row)
        self.assertTrue(table.strings.startswith(b'\0native\0'))
        self.assertEqual(table.string('native'), 1)
        self.assertEqual(table.string('new'), 8)

    def test_bad_boundaries_and_duplicate_new_keys_fail_closed(self):
        raw = dbc(2, 2, [b'\x01\x01'])
        for bad in (raw[:-1], raw+b'\0', b'XXXX'+raw[4:]):
            with self.assertRaises(ValueError):
                assets.DBC(bad, 2, 2)
        with self.assertRaisesRegex(ValueError, 'collision'):
            assets.DBC(raw, 2, 2).append([[22, 1], [22, 1]], key=tuple)
        for name in ('../file', '/file', 'a/../file', 'a//file'):
            with self.assertRaises(ValueError):
                assets.norm(name)

    def test_palette_fourth_byte_is_not_texel_alpha(self):
        for depth, alpha, expected in [(0, b'', [255, 255]), (1, b'\x02', [0, 255]),
                                      (4, b'\xf1', [17, 255]), (8, b'\x07\x80', [7, 128])]:
            header = struct.pack('<4sI4B2I', b'BLP2', 1, 1, depth, 0, 0, 2, 1)
            header += struct.pack('<16I', 1172, *([0]*15))
            header += struct.pack('<16I', 2+len(alpha), *([0]*15))
            palette = b'\x03\x02\x01\x00'+b'\x06\x05\x04\xff'+bytes(1016)
            rgba = assets.palette_rgba(header+palette+b'\0\1'+alpha)
            self.assertEqual(rgba[0:3], b'\1\2\3')
            self.assertEqual(rgba[4:7], b'\4\5\6')
            self.assertEqual(list(rgba[3::4]), expected)

    def test_publication_refuses_unknown_destination(self):
        # No assets are copied: the guard fires before source access or mkdir.
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'client_patches/new-races/primary').mkdir(parents=True)
            with patch.object(assets, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'already exists'):
                    assets.publish_output(root/'does-not-exist')

    def test_parenthesized_ordinary_members_are_preserved(self):
        self.assertEqual(assets.ordinary_names(['(listfile)', '(attributes)', '(custom).bin', 'a.dbc']),
                         ['(custom).bin', 'a.dbc'])
        with self.assertRaisesRegex(ValueError, 'Signed baseline'):
            assets.ordinary_names(['(signature)', 'a.dbc'])

    def test_dxt_alpha_and_color_proof_decoder(self):
        # A DXT5 block: red endpoint selected throughout; explicit alpha255.
        header = struct.pack('<4sI4B2I', b'BLP2', 1, 2, 8, 7, 0, 4, 4)
        header += struct.pack('<16I', 148, *([0]*15))
        header += struct.pack('<16I', 16, *([0]*15))
        block = bytes([255, 0])+bytes(6)+struct.pack('<HHI', 0xf800, 0x001f, 0)
        self.assertEqual(assets.blp_rgba(header+block), bytes([255, 0, 0, 255])*16)

    def test_legacy_proof_rejects_changed_controls_missing_options_and_fallback(self):
        with patch.object(assets, 'blp_rgba', side_effect=lambda raw: raw), patch.object(assets, 'require_absent'):
            for change, message in [('show_scalp', 'controls differ'), ('combination', 'Incomplete source'),
                                    ('fallback', 'Unexpected source scalp fallback')]:
                with self.subTest(change=change), self.assertRaisesRegex(ValueError, message):
                    assets.verify_legacy_hair(hair_proof_fixture(change))
            proof = assets.verify_legacy_hair(hair_proof_fixture())
            self.assertEqual(proof['source_rows_restored'], 320)
            self.assertEqual(len(proof['hair_comparisons']), 11)
            self.assertTrue(all(not c['rgba_exact'] and c['rgba_max_absolute_error'] == 1 for c in proof['hair_comparisons']))

    def test_direct_probe_rejects_present_or_unresolved_native_asset(self):
        result = SimpleNamespace(returncode=0, stdout='', stderr='# extracted 1 files\n')
        with patch.object(assets.subprocess, 'run', return_value=result):
            with self.assertRaisesRegex(ValueError, 'placeholder exists or direct probes failed'):
                assets.require_absent('native.mpq', {r'Character\BloodElf\ScalpLowerHair00_00.blp'})

    def test_publication_requires_complete_four_archive_evidence_before_writes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); evidence = root/'validation.json'
            for archives in ({}, {'primary/Data/patch-Z.mpq': '0'*64}):
                evidence.write_text(json.dumps({'status': 'PASS', 'source_builds': 2, 'archives': archives}))
                for replace_known in (False, True):
                    with self.subTest(archives=len(archives), upgrade=replace_known), patch.object(assets, 'ROOT', root):
                        with self.assertRaisesRegex(ValueError, 'exactly all four'):
                            assets.publish_output(root/'nonexistent', evidence, replace_known)
                        self.assertFalse((root/'client_patches').exists())


def validate_eye_delta(before, after):
    """Independent byte allowlist: exactly22 column7 uint32s, no other bytes."""
    assets.require(before[:20] == after[:20] and len(before) == len(after), 'Facial header/length changed')
    old = assets.DBC(before, 8, 32)
    new = assets.DBC(after, 8, 32)
    assets.require(len(old.rows) == len(new.rows) == 270 and old.strings == new.strings,
                   'Facial count/strings changed')
    changes = []
    for a, b in zip(old.values(), new.values()):
        if a[0] == 22:
            assets.require(a[7] == 0 and b == a[:7]+[2], 'Unexpected High Elf facial delta')
            changes.append(tuple(a[:3]))
        else:
            assets.require(a == b, 'Non22 facial row changed')
    assets.require(len(changes) == 22 and set(changes) ==
                   {(22, s, f) for s in (0, 1) for f in range(11)}, 'Incomplete eye delta keys')


def validate_opacity_delta(before, after, sex):
    """Independent field allowlist; never trust postprocessor offsets/reports."""
    assets.require(len(before) == len(after), 'Opacity model length changed')
    count, start = struct.unpack_from('<2I', before, 88)
    assets.require(count == 3, 'Wrong weight count')
    n, descriptors = struct.unpack_from('<2I', before, start+20+12)
    assets.require(n == (409 if sex == 'Male' else 410), 'Wrong eye track count')
    offsets = []
    for i in range(n):
        k, p = struct.unpack_from('<2I', before, descriptors+i*8)
        offsets.extend(range(p, p+k*2, 2))
    assets.require(len(set(offsets)) == len(offsets) == (816 if sex == 'Male' else 410), 'Wrong eye key count')
    restored = bytearray(after)
    for p in offsets:
        a, b = struct.unpack_from('<h', before, p)[0], struct.unpack_from('<h', after, p)[0]
        assets.require(a in ({6553, 32767} if sex == 'Male' else {19660}) and b == 6553,
                       'Eye keys must normalize exactly to native6553')
        restored[p:p+2] = before[p:p+2]
    assets.require(bytes(restored) == before, 'Non-opacity model bytes changed')
    assets.require(sum(a != b for a, b in zip(before, after)) == (1624 if sex == 'Male' else 820),
                   'Unexpected opacity changed-byte count')
    return {'keys': len(offsets), 'changed_bytes': 1624 if sex == 'Male' else 820,
            'all_other_bytes_exact': True}


def prior_archive(candidate, name):
    if candidate.resolve() == (assets.ROOT/'client_patches/new-races').resolve():
        return assets.publication_path(name)
    return candidate/name


def previous_publication_root(output, manifest, previous_publication=None):
    relatives = [f'{edition}/{relative}' for edition in ('primary', 'optional-extra-skins')
                 for relative in ('Data/patch-Z.mpq', 'Data/esES/patch-esES-Z.MPQ')]
    expected = {name: manifest['previous_publication'][name] for name in relatives}
    candidates = ([Path(previous_publication)] if previous_publication is not None else
                  [assets.ROOT/'client_patches/new-races', output/'pass1/replaced-publication'])
    failures = []
    for candidate in candidates:
        candidate = candidate.resolve()
        mismatches = []
        for name, digest in expected.items():
            try:
                matches = assets.file_sha(prior_archive(candidate, name)) == digest
            except OSError:
                matches = False
            if not matches:
                mismatches.append(name)
        if not mismatches:
            return candidate
        failures.append(f'{candidate}: missing or wrong SHA256: {", ".join(mismatches)}')
    raise ValueError('Texture-only comparison requires all four exact known prior archives. '
                     'Supply --previous-publication DIR pointing to the retained backup. '
                     + '; '.join(failures))


def integration(output, verify_existing=False, previous_publication=None):
    output = output.resolve()
    assets.require(output.is_relative_to(assets.ROOT/'work'), 'work/ output required')
    manifest = json.loads(assets.MANIFEST.read_text())
    prior_root = previous_publication_root(output, manifest, previous_publication)
    converter = assets.ROOT/'work/toolchains/new-races-model-converter/NewRacesModelConverter.dll'
    dotnet = os.environ.get('DOTNET', 'dotnet')
    if verify_existing:
        reports = [json.loads((output/f'pass{i}/report.json').read_text()) for i in (1, 2)]
    else:
        assets.require(not output.exists(), 'Fresh work/ output required')
        output.mkdir(parents=True)
        reports = [assets.build(output/f'pass{i}', converter, dotnet) for i in (1, 2)]
    sources = assets.Sources(manifest)
    result = {'status': 'PASS', 'runtime': 'NOT RUN', 'archives': {}, 'preservation': {}, 'source_builds': 2}
    result['previous_publication'] = str(prior_root)
    required_exe = '87ceca9ea08da2f0d9d312d833ae76751a3ab8f2b8a7d742bfd2356e55f291f3'
    for report in reports:
        assets.require(report['glue']['required_executable_sha256'] == required_exe and
                       report['glue']['required_executable_profile'] == 'cache-plus-custom-gluexml (--allow-custom-gluexml)',
                       'Glue requires the combined executable profile, not the cache-only derivative')
        assets.require(report['build_tools_sha256']['tools/build_new_races_glue.py'] ==
                       assets.file_sha(assets.ROOT/'tools/build_new_races_glue.py'), 'Stale Glue builder report')
        assets.require(report['model_toolchain']['converter_sha256'] == assets.file_sha(converter) ==
                       report['model_toolchain']['build_manifest']['sha256'][str(converter.relative_to(assets.ROOT))],
                       'Converter/build-manifest/report hash linkage mismatch')
    assets.require(reports[0]['glue'] == reports[1]['glue'] and
                   reports[0]['model_toolchain'] == reports[1]['model_toolchain'], 'Nondeterministic tool/profile evidence')
    result['required_executable_sha256'] = required_exe
    result['glue_profile_and_model_toolchain'] = 'PASS (static metadata and build hashes; runtime NOT RUN)'
    from test_new_races_models import validate as validate_model
    result['model_binary_validation'] = {}
    result['texture_only_comparison'] = {}
    for i, spec in enumerate(manifest['models']):
        model_results = []
        for iteration in (1, 2):
            build_root = output/f'pass{iteration}'
            model_results.append(validate_model(build_root/'model-inputs'/f'{i}.m2', build_root/'models'/spec['target']))
            meta = reports[iteration-1]['models'][str(91000+i)]
            assets.require(assets.file_sha(build_root/'models'/spec['target']) ==
                           meta['converter_intermediate_sha256'], 'Converter intermediate/report SHA mismatch')
            if spec['race'] == 22:
                from high_elf_eye_opacity import PINS
                sex = ('Male', 'Female')[spec['sex']]
                post = meta['eye_opacity_postprocess']
                assets.require((post['source_sha256'], post['final_sha256']) == PINS[sex][:2] and
                               meta['packaged_sha256'] == post['final_sha256'], 'Opacity provenance mismatch')
        assets.require(model_results[0] == model_results[1], 'Model validation differs between source builds')
        result['model_binary_validation'][str(91000+i)] = model_results[0]
    for edition in ('primary', 'optional-extra-skins'):
        assets.require(reports[0]['status'] == 'CLIENT-ONLY PREVIEW CANDIDATE; NOT SERVER-CREATABLE', 'Wrong preview status')
        deferred = reports[0]['editions'][edition]['deferred_cosmetic_rows']
        assets.require(not deferred, 'Ordinary source hair rows must not be deferred')
        for relative in ('Data/patch-Z.mpq', 'Data/esES/patch-esES-Z.MPQ'):
            paths = [output/f'pass{i}'/edition/relative for i in (1, 2)]
            hashes = [assets.file_sha(p) for p in paths]
            assets.require(hashes[0] == hashes[1], f'Non-deterministic MPQ: {edition}/{relative}: {hashes}')
            result['archives'][edition+'/'+relative] = hashes[0]
            for table, schema in assets.SCHEMAS.items():
                member = 'DBFilesClient\\'+table+'.dbc'
                raw = assets.extract(paths[0], member)
                after = assets.DBC(raw, *schema)
                key = edition+':'+table if table in ('CharSections', 'CharacterFacialHairStyles') else 'native:'+table
                before = assets.DBC(sources.get(key), *schema)
                assets.require(after.rows[:len(before.rows)] == before.rows, 'Old row bytes changed')
                assets.require(after.strings.startswith(before.strings), 'Old string prefix changed')
                if table == 'CharBaseInfo':
                    assets.require(len(after.rows) == 83 and after.values()[72:] ==
                                   [[r, c] for r, classes in assets.CLASSES.items() for c in classes], 'Class contract mismatch')
                if table == 'ChrRaces':
                    rows = {r[0]: r for r in after.values()}
                    for race, faction, file_string in ((22, 1, 'TurtleHighElf'), (23, 2, 'TurtleGoblin')):
                        assets.require(rows[race][2] == faction and rows[race][68] == 0 and
                                       after.text(rows[race][11]) == file_string, 'Identity/faction/expansion mismatch')
                    assets.require(after.text(rows[22][20]) == 'Alto Elfo', 'Missing explicit esES name')
                if table == 'CharSections':
                    section_keys = [tuple(r[i] for i in (1, 2, 3, 8, 9)) for r in after.values()]
                    assets.require(section_keys == sorted(section_keys), 'Delivered CharSections physical keys are not fully sorted')
                    suffix = after.values()[len(before.rows):]
                    assets.require([r[1] for r in suffix] == sorted(r[1] for r in suffix) and
                                   suffix[0][1] == 22 and suffix[-1][1] == 23, 'New race groups must be22 then23')
                    original = assets.DBC(sources.get('source:CharSections'), 10, 40)
                    selected = [r for r in original.values() if r[1] in (9, 10) and r[9] == 0]
                    expected_ids = {(22 if r[1] == 10 else 23, r[2], r[3], r[4], r[5]): 22000+i
                                    for i, r in enumerate(selected)}
                    assets.require({tuple(r[i] for i in (1, 2, 3, 8, 9)): r[0] for r in suffix} == expected_ids,
                                   'Physical sorting renumbered source-order customization IDs')
                    hair = [r for r in after.values() if r[1:4] == [22, 1, 3]]
                    assets.require(len(hair) == 320 and {(r[8], r[9]) for r in hair} ==
                                   {(s, c) for s in range(20) for c in range(16)}, 'Missing female hair options')
                    assets.require(len(after.rows) == (10490 if edition == 'primary' else 10640), 'Incorrect restored section count')
                    original = assets.DBC(sources.get('source:CharSections'), 10, 40)
                    source_hair = {(r[4], r[5]): r for r in original.values() if r[1:4] == [10, 1, 3] and r[9] == 0}
                    for row in hair:
                        src = source_hair[(row[8], row[9])]
                        member = after.text(row[4])
                        assets.require(row[4] != 0 and row[5:7] == [0, 0], 'Incorrect no-scalp hair slots')
                        assets.require(assets.extract(paths[0], member) == sources.get('texture:'+original.text(src[6]).lower()),
                                       'Valid source hair Texture1 changed or lost')
                if table == 'CharHairGeosets':
                    suffix = after.values()[len(before.rows):]
                    assets.require([tuple(r[1:4]) for r in suffix] == sorted(tuple(r[1:4]) for r in suffix),
                                   'New hair geoset rows not naturally sorted')
                    choices = [r for r in after.values() if r[1:3] == [22, 1]]
                    assets.require(len(after.rows) == 406 and len(choices) == 20 and
                                   {tuple(r[3:]) for r in choices} == {(s, s+2, 0) for s in range(20)},
                                   'Missing or changed female hair geoset/ShowScalp controls')
                    native = assets.DBC(sources.get('native:CharHairGeosets'), 6, 24)
                    assets.require({tuple(r[3:]) for r in native.values() if r[1:3] == [10, 1]} ==
                                   {tuple(r[3:]) for r in choices}, 'Native no-scalp controls do not match delivered choices')
                if table == 'CharacterFacialHairStyles':
                    assets.require(fix_selectors(raw, {(22, s): {1702} for s in (0, 1)}) == raw,
                                   'Delivered High Elf eye selectors are not fixed')
                    suffix = after.values()[len(before.rows):]
                    assets.require([tuple(r[:3]) for r in suffix] == sorted(tuple(r[:3]) for r in suffix),
                                   'New facial style rows not naturally sorted')
                if table == 'CreatureModelData':
                    old = {r[0]: r for r in before.values()}
                    new = {r[0]: r for r in after.values()}
                    for i, donor in enumerate((2208, 2209, 831, 832)):
                        row = new[91000+i]
                        assets.require(row[1] == old[donor][1] and all(row[c] == old[donor][c] for c in range(28)
                                       if c not in (0, 2, 4, 17, 18, 19, 20, 21, 22)),
                                       'New ModelData flags or other unknown donor fields changed')
                result['preservation'][edition+'/'+table] = {'old_rows': len(before.rows), 'total_rows': len(after.rows),
                                                            'old_rows_and_string_prefix': 'byte-exact'}
            archive_report = reports[0]['editions'][edition]['archives'][relative]
            base = sources.archive(manifest['baselines']['locale' if 'esES/' in relative else 'root'])
            # Independent baseline inventory: do not trust a builder-filtered report.
            baseline_names = [n for n in assets.listing(base) if n.lower() not in ('(listfile)', '(attributes)')]
            delivered_names = {assets.norm(n).lower() for n in assets.listing(paths[0])}
            changed = {n.lower() for n in archive_report['payload']}
            for name in baseline_names:
                assets.require(assets.norm(name).lower() in delivered_names, 'Baseline archive member lost')
                if assets.norm(name).lower() not in changed:
                    assets.require(assets.extract(base, name) == assets.extract(paths[0], name), 'Unrelated member not byte-exact')
            for name, digest in archive_report['unrelated_members_preserved'].items():
                raw = assets.extract(paths[0], name.replace('/', '\\'))
                assets.require(assets.sha(raw) == digest, 'Unrelated archive member changed')
            # Independently read all packaged new resources from both winning archives.
            for name, info in archive_report['payload'].items():
                raw = assets.extract(paths[0], name.replace('/', '\\'))
                assets.require(raw is not None and assets.sha(raw) == info['sha256'], 'Packaged resource mismatch')
                for i, spec in enumerate(manifest['models']):
                    if name.lower() == spec['target'].lower():
                        assets.require(assets.sha(raw) == reports[0]['models'][str(91000+i)]['packaged_sha256'],
                                       'Packaged model/report SHA mismatch')
            # Compare actual previous delivery, not just source baselines or reports.
            old = prior_archive(prior_root, edition+'/'+relative)
            assets.require(assets.file_sha(old) == manifest['previous_publication'][edition+'/'+relative],
                           'Texture-only comparison requires exact known prior archive')
            old_names = {assets.norm(n).lower(): n for n in assets.ordinary_names(assets.listing(old))}
            new_names = {assets.norm(n).lower(): n for n in assets.ordinary_names(assets.listing(paths[0]))}
            assets.require(old_names.keys() == new_names.keys(), 'Texture-only inventory changed')
            actual_payload, differences = {}, []
            expected_changes = {n.lower() for n, meta in reports[0]['blp_metadata'].items()
                                if 'formatNormalizations' in meta}
            facial_member = 'dbfilesclient/characterfacialhairstyles.dbc'
            assets.require(len(expected_changes) == 44, 'Expected exactly44 normalized textures')
            expected_changes.add(facial_member)
            eye_members = {f'character/custom/turtlehighelf/{s}/turtlehighelf{s}.m2'.lower(): s
                           for s in ('Male', 'Female')}
            expected_changes.update(eye_members)
            for low, name in new_names.items():
                after_raw = assets.extract(paths[0], name)
                before_raw = assets.extract(old, old_names[low])
                if after_raw != before_raw:
                    differences.append(low)
                    assets.require(low in expected_changes, 'Non-allowlisted payload changed: '+name)
                    if low == facial_member:
                        validate_eye_delta(before_raw, after_raw)
                        continue
                    if low in eye_members:
                        validate_opacity_delta(before_raw, after_raw, eye_members[low])
                        continue
                    from build_forest_troll_skins import validate_blp
                    bm, am = validate_blp(before_raw), validate_blp(after_raw)
                    assets.require([(m['width'], m['height']) for m in bm['mips']] ==
                                   [(m['width'], m['height']) for m in am['mips']], 'Mip dimensions/count changed')
                    for level in range(len(bm['mips'])):
                        assets.require(assets.blp_rgba(before_raw, level)[3::4] ==
                                       assets.palette_rgba(after_raw, level)[3::4], 'Source mip alpha drift')
                if low in {n.lower() for n in archive_report['payload']}:
                    actual_payload[assets.norm(name)] = after_raw
            assets.require(len(differences) == 47 and set(differences) == expected_changes,
                           'Expected exactly44 textures,22 facial eye selector fields and2 eye-opacity models')
            result['texture_only_comparison'][edition+'/'+relative] = {
                'old_sha256': assets.file_sha(old), 'changed_members': sorted(differences),
                'unchanged_members': len(new_names)-47, 'all_mip_alpha_exact': True,
                'cpu_roles': assets.validate_compositor(actual_payload)}
        # Root and locale contain identical new table/art/Glue payloads.
        a, b = reports[0]['editions'][edition]['archives'].values()
        assets.require(a['payload'] == b['payload'], 'Root/locale contribution drift')
    # Reading all original archive hashes again establishes no source-file changes.
    for name, digest in manifest['archives'].items():
        path = Path(name) if Path(name).is_absolute() else assets.ROOT/name
        assets.require(assets.file_sha(path) == digest, 'Original archive changed during builds')
    assets.dump(output/'validation.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--integration', type=Path)
    parser.add_argument('--verify-existing', action='store_true')
    parser.add_argument('--previous-publication', type=Path,
                        help='Retained prior delivery directory; all four pinned archive hashes required')
    args, rest = parser.parse_known_args()
    if args.integration:
        integration(args.integration, args.verify_existing, args.previous_publication)
    else:
        unittest.main(argv=[__file__, *rest])
