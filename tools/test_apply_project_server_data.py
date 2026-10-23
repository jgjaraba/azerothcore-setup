"""Synthetic binary fixtures and fake-mysql shell integration; no live DB access."""
import sys
sys.dont_write_bytecode = True

import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import apply_project_server_data as app
from crypt_release_dbc import parse_dbc


ROOT = Path(__file__).resolve().parent.parent


def dbc(fields, rows):
    return (struct.pack('<4s4I', b'WDBC', len(rows), fields, fields * 4, 1) +
            b''.join(struct.pack(f'<{fields}I', *r) for r in rows) + b'\0')


class ServerDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'server'
        self.target = self.root / 'target'
        self.state = self.root / 'state'
        self.manifest = self.source / 'manifest.json'
        self.originals = {}
        files = {}
        for name, (fields, ids, _, _) in app.DELTAS.items():
            base = [0] * fields
            base[0] = 1
            target = self.target / 'dbc' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(dbc(fields, [base]))
            self.originals[target] = target.read_bytes()
            rows = []
            for ident in ids:
                row = [0] * fields
                row[0] = ident
                if name != 'Map.dbc':
                    row[1] = 800
                if name == 'WorldMapArea.dbc':
                    row[2] = 5086
                rows.append(row)
            self.add_source(files, 'dbc/' + name, dbc(fields, rows), 'dbc-delta')
        terrain = b'MAPS' + struct.pack('<II', 9, 12340)
        tile = bytearray(64)
        struct.pack_into('<4I', tile, 0, 0x4d4d4150, 7, 20, 8)
        struct.pack_into('<II', tile, 56, 0x444e4156, 7)
        for name, raw in {'maps/0000000.map': terrain, 'vmaps/000.vmtree': b'VMAP_4.8',
                          'mmaps/0000000.mmtile': bytes(tile), 'mmaps/000.mmap': bytes(28)}.items():
            path = self.target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        self.add_source(files, 'maps/8000000.map', terrain + b'pilot', 'copy')
        self.add_source(files, 'vmaps/shared.vmo', b'VMAP_4.8model', 'copy')
        self.files = files
        self.write_manifest()

    def add_source(self, files, name, raw, kind):
        source = self.source / 'turtle-crypt' / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(raw)
        files['turtle-crypt/' + name] = dict(path=name, size=len(raw), sha256=app.sha(raw), kind=kind)

    def write_manifest(self):
        self.manifest.write_bytes(app.json_bytes(dict(schema=1, files=self.files)))

    def install(self, **kwargs):
        return app.install(self.manifest, self.target, self.state, offline=True, **kwargs)

    def rollback(self, **kwargs):
        return app.rollback(self.manifest, self.target, self.state, offline=True, **kwargs)

    def add_facial_styles(self):
        # Race is not an ID: both repeated races and repeated (race, sex) are valid.
        rows = [(8, 0, 0, 0, 1, 0, 0, 0), (1, 0, 0, 0, 0, 0, 0, 0),
                (8, 1, 0, 0, 1, 0, 0, 0)]
        target = self.target / app.FACIAL_STYLE_TARGET
        target.write_bytes(dbc(8, rows))
        self.originals[target] = target.read_bytes()
        donor = dbc(8, [key + values for key, values in app.FACIAL_STYLE_ROWS.items()])
        self.add_source(self.files, app.FACIAL_STYLE_TARGET, donor, 'facial-style-delta')
        self.write_manifest()
        return target, donor

    def test_natural_styles_plan_install_repeat_and_exact_rollback(self):
        target, donor = self.add_facial_styles()
        original = target.read_bytes()
        result, outputs = app.plan(self.manifest, self.target, self.state)
        merged = outputs[app.FACIAL_STYLE_TARGET]
        self.assertEqual(len(result['files']), 8)
        self.assertEqual(target.read_bytes(), original)
        self.assertFalse(self.state.exists())
        self.assertNotEqual(merged, donor)
        self.assertEqual(merged[20:20 + 3 * 32], original[20:-1])
        rows, block = app.parse_natural_dbc(merged)
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[3:], app.parse_natural_dbc(donor)[0])
        self.assertEqual(block, b'\0')
        self.assertEqual(self.install()['status'], 'installed')
        self.assertEqual(target.read_bytes(), merged)
        self.assertEqual(self.install()['status'], 'already-installed')
        self.assertEqual(app.plan(self.manifest, self.target)[1][app.FACIAL_STYLE_TARGET], merged)
        self.rollback()
        for path, raw in self.originals.items():
            self.assertEqual(path.read_bytes(), raw)

    def test_natural_styles_conflict_duplicates_and_missing_target(self):
        target, donor = self.add_facial_styles()
        original = target.read_bytes()
        rows, _ = app.parse_natural_dbc(original)
        conflict = list(app.parse_natural_dbc(donor)[0][0])
        conflict[4] += 1
        target.write_bytes(dbc(8, rows + [conflict]))
        with self.assertRaisesRegex(ValueError, 'Natural-key DBC collision'):
            self.install()
        target.write_bytes(dbc(8, rows + rows[:1]))
        with self.assertRaisesRegex(ValueError, 'Duplicate natural-key'):
            self.install()
        target.unlink()
        with self.assertRaises(FileNotFoundError):
            self.install()
        self.assertFalse(self.state.exists())

    def test_natural_styles_source_guards(self):
        _, donor = self.add_facial_styles()
        rows, _ = app.parse_natural_dbc(donor)
        bad_key = list(rows[0])
        bad_key[0] = 1
        bad_geoset = list(rows[0])
        bad_geoset[4] += 1
        for invalid, message in [(rows + rows[:1], 'Duplicate natural-key'),
                                 (rows[:-1], 'seven Troll'),
                                 ([bad_key] + rows[1:], 'seven Troll'),
                                 ([bad_geoset] + rows[1:], 'seven Troll')]:
            with self.subTest(message=message, rows=invalid):
                self.add_source(self.files, app.FACIAL_STYLE_TARGET,
                                dbc(8, invalid), 'facial-style-delta')
                self.write_manifest()
                with self.assertRaisesRegex(ValueError, message):
                    app.inventory(self.manifest)
        key = 'turtle-crypt/' + app.FACIAL_STYLE_TARGET
        self.files[key]['path'] = 'dbc/Other.dbc'
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'Unknown facial-style'):
            app.inventory(self.manifest)

    def test_natural_styles_strict_wdbc_parser(self):
        valid = dbc(8, [(8, 0, 0, 0, 0, 0, 0, 0)])
        invalid = [b'', valid[:19], b'WDB2' + valid[4:], valid[:-1], valid + b'\0',
                   valid[:-1] + b'x', valid[:-1] + b'\0x\0']
        for offset, value in [(8, 9), (12, 36), (16, 0), (4, 2)]:
            raw = bytearray(valid)
            struct.pack_into('<I', raw, offset, value)
            invalid.append(bytes(raw))
        # Declared string blocks must start AND end with NUL.
        for block in (b'x\0', b'\0x'):
            raw = bytearray(valid[:-1] + block)
            struct.pack_into('<I', raw, 16, len(block))
            invalid.append(bytes(raw))
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                app.parse_natural_dbc(raw)
        # No strings are referenced, but the native block must survive exactly.
        native = bytearray(valid[:-1] + b'\0unused\0')
        struct.pack_into('<I', native, 16, 8)
        merged = app.merge_natural_dbc(bytes(native), dbc(8, []))
        self.assertEqual(merged, bytes(native))

    def test_natural_styles_incomplete_state_and_recovery(self):
        target, _ = self.add_facial_styles()
        self.state.mkdir()
        with self.assertRaisesRegex(ValueError, 'before journal'):
            self.install()
        self.state.rmdir()
        real_atomic = app.target_atomic

        def interrupted(item, raw):
            real_atomic(item, raw)
            if item['path'] == str(target):
                raise OSError('interrupted after natural styles')

        with patch.object(app, 'target_atomic', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'interrupted'):
                self.install()
        self.assertNotEqual(target.read_bytes(), self.originals[target])
        self.rollback(recovery=True)
        for path, raw in self.originals.items():
            self.assertEqual(path.read_bytes(), raw)

    def test_repository_natural_style_delta_against_native_when_available(self):
        native = ROOT / 'dbc/CharacterFacialHairStyles.dbc'
        donor = ROOT / 'data/server/turtle-customizations/dbc/CharacterFacialHairStyles.dbc'
        if not native.is_file() or not donor.is_file():
            self.skipTest('Repository native/donor DBCs unavailable')
        raw = native.read_bytes()
        self.assertEqual(app.sha(raw),
                         'd67bfb0a674af83dab5301ab686a534ec888fae7b52a91045213e111a2399554')
        merged = app.merge_natural_dbc(raw, donor.read_bytes())
        self.assertEqual(len(app.parse_natural_dbc(raw)[0]), 222)
        self.assertEqual(len(app.parse_natural_dbc(merged)[0]), 222 + len(app.parse_natural_dbc(donor.read_bytes())[0]))
        self.assertEqual(merged[20:20 + 222 * 32], raw[20:20 + 222 * 32])
        self.assertEqual(app.merge_natural_dbc(merged, donor.read_bytes()), merged)

    def test_plan_is_readonly_and_merge_preserves_native_rows(self):
        result, outputs = app.plan(self.manifest, self.target, self.state)
        self.assertFalse(self.state.exists())
        self.assertFalse((self.target / 'maps/8000000.map').exists())
        self.assertEqual(len(result['files']), 7)
        for name in app.DELTAS:
            base = self.originals[self.target / 'dbc' / name]
            fields, rows, _ = parse_dbc(outputs['dbc/' + name])
            self.assertEqual(rows[0], parse_dbc(base)[1][0])
            self.assertEqual(len(rows), 1 + len(app.DELTAS[name][1]))

    def test_install_repeat_and_file_only_rollback(self):
        shared = self.target / 'vmaps/shared.vmo'
        shared.write_bytes(b'VMAP_4.8model')
        os.chmod(self.target / 'dbc/Map.dbc', 0o640)
        self.assertEqual(self.install()['status'], 'installed')
        first = (self.target / 'dbc/Map.dbc').read_bytes()
        self.assertEqual(self.install()['status'], 'already-installed')
        self.assertEqual((self.target / 'dbc/Map.dbc').read_bytes(), first)
        # Fresh state also accepts semantically installed DBCs and identical copies.
        app.plan(self.manifest, self.target)
        self.assertEqual(self.rollback()['scope'], 'files-only')
        for path, original in self.originals.items():
            self.assertEqual(path.read_bytes(), original)
        self.assertEqual((self.target / 'dbc/Map.dbc').stat().st_mode & 0o777, 0o640)
        self.assertFalse((self.target / 'maps/8000000.map').exists())
        self.assertEqual(shared.read_bytes(), b'VMAP_4.8model')
        self.assertEqual(self.rollback()['status'], 'already-rolled-back')

    def test_expected_plan_catches_drift_before_state_creation(self):
        expected, _ = app.plan(self.manifest, self.target)
        path = self.root / 'plan.json'
        path.write_bytes(app.json_bytes(expected))
        # Add an unrelated, valid native row. The new merge would be compatible,
        # but its exact pre-SQL hash must not be silently recalculated.
        target = self.target / 'dbc/Map.dbc'
        fields, rows, _ = parse_dbc(target.read_bytes())
        rows.append([2] + [0] * (fields - 1))
        target.write_bytes(dbc(fields, rows))
        with self.assertRaisesRegex(ValueError, 'since pre-SQL'):
            self.install(expected_plan=path)
        self.assertFalse(self.state.exists())

    def test_collision_and_offline_have_no_writes(self):
        (self.target / 'maps/8000000.map').write_bytes(b'other')
        with self.assertRaisesRegex(ValueError, 'collision'):
            self.install()
        with self.assertRaisesRegex(ValueError, '--offline'):
            app.install(self.manifest, self.target, self.state)
        self.assertFalse(self.state.exists())

    def test_changed_owned_file_blocks_entire_rollback(self):
        self.install()
        owned = self.target / 'vmaps/shared.vmo'
        owned.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Owned file changed'):
            self.rollback()
        self.assertTrue((self.target / 'maps/8000000.map').exists())

    def test_recover_partial_install_and_partial_rollback(self):
        real_atomic = app.target_atomic
        written = []

        def interrupted(item, raw):
            real_atomic(item, raw)
            written.append(item['path'])
            if len(written) == 2:
                raise OSError('simulated interruption')

        with patch.object(app, 'target_atomic', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'interruption'):
                self.install()
        journal = json.loads((self.state / 'journal.json').read_text())
        self.assertEqual(journal['phase'], 'prepared')
        with self.assertRaisesRegex(ValueError, 'recover'):
            self.install()
        with self.assertRaisesRegex(ValueError, 'recover'):
            self.rollback()
        written.clear()
        with patch.object(app, 'target_atomic', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'interruption'):
                self.rollback(recovery=True)
        self.assertEqual(self.rollback(recovery=True)['status'], 'rolled-back')
        for path, original in self.originals.items():
            self.assertEqual(path.read_bytes(), original)

    def test_recover_interrupted_temporary_write(self):
        def interrupted(item, raw):
            Path(item['temporary']).write_bytes(raw[:10])
            raise OSError('simulated process death during temporary write')

        with patch.object(app, 'target_atomic', side_effect=interrupted):
            with self.assertRaises(OSError):
                self.install()
        self.assertTrue(list(self.target.rglob('.project-server-data-*')))
        self.rollback(recovery=True)
        self.assertFalse(list(self.target.rglob('.project-server-data-*')))
        for path, original in self.originals.items():
            self.assertEqual(path.read_bytes(), original)

    def test_recovery_syncs_already_removed_nested_directories(self):
        self.install()
        journal_path = self.state / 'journal.json'
        journal = json.loads(journal_path.read_text())
        # Simulate a rollback interrupted after rmdir of nested owned directories,
        # but before syncing the surviving parent. The directory entries remain
        # in its durable intent even though neither directory currently exists.
        journal['directories'] = [str(self.target / 'owned'), str(self.target / 'owned/nested')]
        journal['phase'] = 'rollback_intent'
        journal_path.write_bytes(app.json_bytes(journal))
        with patch.object(app, 'fsync_dir', wraps=app.fsync_dir) as sync:
            self.rollback(recovery=True)
        self.assertIn(unittest.mock.call(self.target), sync.call_args_list)

    def test_incomplete_preparation_backup_tamper_and_identity(self):
        self.state.mkdir()
        with self.assertRaisesRegex(ValueError, 'before journal'):
            self.install()
        self.state.rmdir()
        self.install()
        backup = self.state / 'backups/0'
        backup.write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError, 'backup changed'):
            self.rollback()

    def test_physical_m2_collision_model_accepted(self):
        raw = b'VMAP_4.8physical collision model'
        self.add_source(self.files, 'vmaps/physical.m2', raw, 'copy')
        self.write_manifest()
        _, payload = app.inventory(self.manifest)
        self.assertEqual(payload['vmaps/physical.m2'], raw)
        self.install()
        self.assertEqual((self.target / 'vmaps/physical.m2').read_bytes(), raw)

    def test_collision_models_reject_client_m2_header(self):
        for suffix in ('.m2', '.vmo'):
            with self.subTest(suffix=suffix):
                self.add_source(self.files, 'vmaps/client' + suffix, b'MD20client model', 'copy')
                self.write_manifest()
                with self.assertRaisesRegex(ValueError, 'collision model header'):
                    app.inventory(self.manifest)
                del self.files['turtle-crypt/vmaps/client' + suffix]
                (self.source / ('turtle-crypt/vmaps/client' + suffix)).unlink()

    def test_m2_only_allowed_under_vmaps(self):
        for directory in ('maps', 'mmaps'):
            with self.subTest(directory=directory):
                name = directory + '/physical.m2'
                self.add_source(self.files, name, b'VMAP_4.8collision', 'copy')
                self.write_manifest()
                with self.assertRaisesRegex(ValueError, 'Unsupported copy target'):
                    app.inventory(self.manifest)
                del self.files['turtle-crypt/' + name]
                (self.source / 'turtle-crypt' / name).unlink()

    def test_strict_inventory(self):
        extra = self.source / 'extra'
        extra.write_bytes(b'x')
        with self.assertRaisesRegex(ValueError, 'coverage'):
            app.inventory(self.manifest)
        extra.unlink()
        source = self.source / next(iter(self.files))
        raw = source.read_bytes()
        source.write_bytes(raw + b'x')
        with self.assertRaisesRegex(ValueError, 'hash/size'):
            app.inventory(self.manifest)
        source.write_bytes(raw)
        extra.symlink_to(source)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            app.inventory(self.manifest)

    def test_unsafe_targets_duplicates_and_overlap(self):
        key = next(iter(self.files))
        original = self.files[key]['path']
        self.files[key]['path'] = '../escape'
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            app.inventory(self.manifest)
        self.files[key]['path'] = original
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            app.plan(self.manifest, self.source / 'target')
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON'):
            app.load_json('{"schema":1,"schema":1}')

    def test_bad_native_header_and_dbc_collision(self):
        sample = self.target / 'maps/0000000.map'
        raw = sample.read_bytes()
        sample.write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError, 'terrain header'):
            self.install()
        sample.write_bytes(raw)
        path = self.target / 'dbc/Map.dbc'
        fields, rows, _ = parse_dbc(path.read_bytes())
        row = [0] * fields
        row[0], row[2] = 800, 999
        path.write_bytes(dbc(fields, rows + [row]))
        with self.assertRaisesRegex(ValueError, 'DBC ID collision'):
            self.install()
        self.assertFalse(self.state.exists())

    def shell(self, *args, mysql_body=None):
        sql = self.root / 'sql'
        sql.mkdir(exist_ok=True)
        (sql / 'manifest.txt').write_text('one.sql\ntwo.sql\n')
        (sql / 'one.sql').write_text('SELECT 1;\n')
        (sql / 'two.sql').write_text('SELECT 2;\n')
        bin_dir = self.root / 'bin'
        bin_dir.mkdir(exist_ok=True)
        mysql = bin_dir / 'mysql'
        mysql.write_text('#!/usr/bin/env python3\nimport os, sys\n'
                         'from pathlib import Path\n'
                         'with open(os.environ["MYSQL_CALLS"], "a") as f:\n'
                         '    f.write(repr(sys.argv[1:]) + " " + sys.stdin.read())\n' +
                         (mysql_body or ''))
        mysql.chmod(0o755)
        env = dict(os.environ, SQL_DIR=str(sql), SERVER_DATA_MANIFEST=str(self.manifest),
                   MYSQL_CALLS=str(self.root / 'mysql-calls'), LOGIN_PATH='fixture-login',
                   PATH=str(bin_dir) + os.pathsep + os.environ['PATH'])
        return subprocess.run(['bash', str(ROOT / 'scripts/apply-db-world.sh'), *args],
                              env=env, capture_output=True, text=True)

    def data_args(self):
        return ['--with-server-data', '--data-dir', str(self.target),
                '--state-dir', str(self.state), '--offline']

    def test_shell_default_and_validate_compatibility(self):
        self.assertEqual(self.shell('--validate').returncode, 0)
        self.assertFalse((self.root / 'mysql-calls').exists())
        result = self.shell()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = (self.root / 'mysql-calls').read_text()
        self.assertIn('--login-path=fixture-login', calls)
        self.assertIn('SELECT 1;', calls)
        self.assertIn('SELECT 2;', calls)
        self.assertFalse(self.state.exists())

    def test_shell_validate_is_static_and_bad_flags_rejected(self):
        result = self.shell('--validate', '--with-server-data', '--data-dir', '/nonexistent')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / 'mysql-calls').exists())
        for args in [('--bad',), ('--state-dir',), ('--with-server-data',),
                     ('--offline',), ('--data-dir', '--validate')]:
            self.assertNotEqual(self.shell(*args).returncode, 0)
        self.assertFalse((self.root / 'mysql-calls').exists())

    def test_shell_preflight_before_sql_and_no_install_on_sql_failure(self):
        collision = self.target / 'maps/8000000.map'
        collision.write_bytes(b'collision')
        self.assertNotEqual(self.shell(*self.data_args()).returncode, 0)
        self.assertFalse((self.root / 'mysql-calls').exists())
        self.assertFalse(self.state.exists())
        collision.unlink()
        result = self.shell(*self.data_args(), mysql_body='sys.exit(7)\n')
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertFalse(self.state.exists())
        self.assertFalse(collision.exists())

    def test_shell_rejects_non_directory_state_ancestor_before_sql(self):
        parent = self.root / 'regular-file'
        parent.write_bytes(b'not a directory')
        self.state = parent / 'child'
        result = self.shell(*self.data_args())
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / 'mysql-calls').exists())

    def test_shell_installs_after_sql_and_repeats(self):
        for _ in range(2):
            result = self.shell(*self.data_args())
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads((self.state / 'journal.json').read_text())['phase'], 'installed')

    def test_shell_refuses_drift_during_sql(self):
        path = self.target / 'dbc/Map.dbc'
        fields, rows, _ = parse_dbc(path.read_bytes())
        replacement = dbc(fields, rows + [[2] + [0] * (fields - 1)])
        body = f'Path({str(path)!r}).write_bytes({replacement!r})\n'
        result = self.shell(*self.data_args(), mysql_body=body)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('since pre-SQL', result.stderr)
        self.assertTrue((self.root / 'mysql-calls').exists())
        self.assertFalse(self.state.exists())


if __name__ == '__main__':
    unittest.main()
