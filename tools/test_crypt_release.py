"""Offline release tests; never connects to any world database."""
import contextlib
import io
import json
from pathlib import Path
import struct
import tempfile
import tarfile
import unittest
from unittest.mock import patch

import crypt_release as release
from crypt_release_client import sha
from crypt_release_server_data import DELTAS, tile_models, binary_check
from crypt_release_server_db import compile_sql, SQL_HASHES, identifier, Database


def dbc(fields, rows=(), strings=b'\0'):
    return (struct.pack('<4s4I', b'WDBC', len(rows), fields, fields * 4, len(strings)) +
            b''.join(struct.pack(f'<{fields}I', *row) for row in rows) + strings)


def put(root, name, raw):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


class FakeDatabase:
    """Transaction model: persist runs while changes are still uncommitted."""
    def __init__(self):
        self.rows = []
        self.transactions = 0
        self.conflict = False
        self.fail_after_commit = False
        self.fail_before_commit = False
        self.uuid = '00000000-0000-0000-0000-000000000001'

    def server_identity(self):
        return self.uuid

    def schema(self, compiled):
        return {'fixture': ['all-columns']}

    def bindings(self):
        if self.conflict:
            raise ValueError('binding conflict')

    def snapshot(self, columns):
        return self.rows.copy()

    def transaction(self, statements, columns, before, persist):
        if before != self.rows:
            raise ValueError('SQL changed')
        result = [] if statements[0].startswith('DELETE') else [f'row{i}' for i in range(10)]
        persist(result)
        if self.fail_before_commit:
            raise OSError('simulated connection loss before commit')
        self.transactions += 1
        self.rows = result
        if self.fail_after_commit:
            raise OSError('simulated lost COMMIT acknowledgement')
        return result


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='crypt-release-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bundle, self.data, self.state = (self.root / n for n in ('bundle', 'data', 'state'))
        self.bundle.mkdir()
        self.data.mkdir()
        for name in release.CODE:
            put(self.bundle, name, (Path(release.__file__).parent / name).read_bytes())
        for name in SQL_HASHES:
            put(self.bundle, 'sql/' + name, (release.ROOT / 'data/sql/custom/db_world' / name).read_bytes())
        for name, (fields, ids, strings, order) in DELTAS.items():
            rows = []
            for ident in ids:
                row = [0] * fields
                row[0] = ident
                if name == 'Map.dbc':
                    row[1] = 1
                elif name != 'AreaTable.dbc':
                    row[1] = 800
                else:
                    row[1] = 800
                rows.append(row)
            put(self.bundle, 'server/dbc/' + name, dbc(fields, rows, b'\0KarazhanCrypt\0'))
            put(self.data, 'dbc/' + name, dbc(fields))
        put(self.data, 'maps/0000000.map', b'MAPS' + struct.pack('<II', 9, 12340))
        put(self.data, 'vmaps/000.vmtree', b'VMAP_4.8')
        put(self.data, 'mmaps/000.mmap', bytes(28))
        tile = struct.pack('<4I', 0x4d4d4150, 7, 20, 8) + bytes(40) + struct.pack('<II', 0x444e4156, 7)
        put(self.data, 'mmaps/0000000.mmtile', tile)
        put(self.bundle, 'server/maps/8000000.map', b'MAPS' + struct.pack('<II', 9, 12340))
        put(self.bundle, 'server/vmaps/shared.m2', b'shared-model')
        put(self.data, 'vmaps/shared.m2', b'shared-model')
        put(self.bundle, 'client/Data/patch-T.MPQ', b'pilot')
        self.client = self.root / 'client'
        put(self.client, 'Data/common.MPQ', b'stock')
        report = dict(target_preflight=dict(archives=[dict(path='common.MPQ', size=5, sha256=sha(b'stock'))]),
                      artifact=dict(sha256=sha(b'pilot')))
        put(self.bundle, 'client/report.json', release.json_bytes(report))
        self.inventory()
        self.db = FakeDatabase()
        self.mockdb = patch.object(release, 'Database', return_value=self.db)
        self.mockdb.start()
        self.addCleanup(self.mockdb.stop)
        self.args = dict(bundle=self.bundle, data_dir=self.data, state=self.state,
                         database='acore_crypt_release_test', client=self.client, offline=True)
        self.original = self.tree(self.data)

    def inventory(self):
        files = {p.relative_to(self.bundle).as_posix(): dict(size=p.stat().st_size, sha256=sha(p.read_bytes()))
                 for p in self.bundle.rglob('*') if p.is_file() and p.name != 'manifest.json'}
        put(self.bundle, 'manifest.json', release.json_bytes(dict(schema=1, kind='crypt-portable-release', files=files)))

    @staticmethod
    def tree(root):
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}

    def test_install_reapply_rollback_and_no_unrelated_loss(self):
        self.assertEqual(release.install(**self.args)['status'], 'installed')
        self.assertEqual(len(self.db.rows), 10)
        journal = json.loads((self.state / 'journal.json').read_text())
        self.assertTrue(any(r['before'] is None for r in journal['files']))
        self.assertEqual(len(journal['db_after']), 10)
        self.assertEqual(release.install(**self.args)['status'], 'already-installed')
        self.assertEqual(self.db.transactions, 1)
        put(self.data, 'maps/unrelated', b'preserve')
        self.assertEqual(release.rollback(**self.args)['status'], 'rolled-back')
        self.assertEqual(release.rollback(**self.args)['status'], 'already-rolled-back')
        actual = self.tree(self.data)
        self.assertEqual(actual.pop('maps/unrelated'), b'preserve')
        self.assertEqual(actual, self.original)
        self.assertFalse((self.client / 'Data/patch-T.MPQ').exists())
        self.assertEqual(self.db.rows, [])

    def assert_preflight_refusal(self):
        before = self.tree(self.data)
        with self.assertRaises(ValueError):
            release.install(**self.args)
        self.assertEqual(self.tree(self.data), before)
        self.assertFalse(self.state.exists())
        self.assertEqual(self.db.transactions, 0)

    def test_offline_required(self):
        self.args['offline'] = False
        self.assert_preflight_refusal()

    def test_fresh_sql_collision_even_identical(self):
        self.db.rows = ['occupied']
        self.assert_preflight_refusal()

    def test_binding_conflict(self):
        self.db.conflict = True
        self.assert_preflight_refusal()

    def test_model_collision(self):
        put(self.data, 'vmaps/shared.m2', b'different')
        self.assert_preflight_refusal()

    def test_pilot_map_file_collision(self):
        put(self.data, 'maps/8000000.map', (self.bundle / 'server/maps/8000000.map').read_bytes())
        self.assert_preflight_refusal()

    def test_unexpected_pilot_tile_collision(self):
        put(self.data, 'maps/8009999.map', b'unknown tile')
        self.assert_preflight_refusal()

    def test_unknown_client_archive(self):
        put(self.client, 'Data/patch-Z.MPQ', b'custom')
        self.assert_preflight_refusal()

    def test_target_locale_override(self):
        put(self.data, 'dbc/esES/Map.dbc', b'override')
        self.assert_preflight_refusal()

    def test_secondary_map_directory_collision(self):
        row = [0] * 66
        row[0], row[1] = 999, 1
        put(self.data, 'dbc/Map.dbc', dbc(66, [row], b'\0KarazhanCrypt\0'))
        self.assert_preflight_refusal()

    def test_modified_installed_file_refuses_reapply_and_rollback(self):
        release.install(**self.args)
        put(self.data, 'dbc/Map.dbc', b'operator-edit')
        for function in (release.install, release.rollback):
            with self.assertRaisesRegex(ValueError, 'Owned file changed'):
                function(**self.args)
        self.assertEqual(self.db.transactions, 1)

    def test_modified_sql_refuses_recovery(self):
        release.install(**self.args)
        self.db.rows[0] = 'operator-edit'
        before = self.tree(self.data)
        with self.assertRaisesRegex(ValueError, 'Owned SQL rows changed'):
            release.rollback(**self.args, recovery=True)
        self.assertEqual(self.tree(self.data), before)

    def test_commit_acknowledgement_loss_is_recoverable(self):
        self.db.fail_after_commit = True
        with self.assertRaises(OSError):
            release.install(**self.args)
        journal = json.loads((self.state / 'journal.json').read_text())
        self.assertEqual(journal['phase'], 'db_intent')
        self.assertEqual(len(journal['db_after']), 10)
        self.assertEqual(self.tree(self.data), self.original)
        self.db.fail_after_commit = False
        release.rollback(**self.args, recovery=True)
        self.assertEqual(self.db.rows, [])
        self.assertEqual(self.tree(self.data), self.original)

    def test_precommit_disconnect_is_recoverable(self):
        self.db.fail_before_commit = True
        with self.assertRaises(OSError):
            release.install(**self.args)
        self.assertEqual(self.db.rows, [])
        self.db.fail_before_commit = False
        release.rollback(**self.args, recovery=True)
        self.assertEqual(self.tree(self.data), self.original)

    def test_recover_does_not_accept_deleted_fully_installed_file(self):
        release.install(**self.args)
        (self.client / 'Data/patch-T.MPQ').unlink()
        with self.assertRaisesRegex(ValueError, 'Owned file changed'):
            release.rollback(**self.args, recovery=True)

    def test_partial_file_write_requires_explicit_recovery(self):
        original_atomic = release.atomic
        def fail(path, raw, *args):
            if str(path).endswith('/dbc/Map.dbc'):
                raise OSError('simulated full disk')
            original_atomic(path, raw, *args)
        with patch.object(release, 'atomic', side_effect=fail):
            with self.assertRaises(OSError):
                release.install(**self.args)
        with self.assertRaisesRegex(ValueError, 'Interrupted'):
            release.rollback(**self.args)
        release.rollback(**self.args, recovery=True)
        self.assertEqual(self.tree(self.data), self.original)

    def test_interrupted_backup_preparation_diagnosed_without_mutations(self):
        original_atomic = release.atomic
        client_before = self.tree(self.client)
        backup_writes = []

        def fail_second_backup(path, raw, *args):
            if Path(path).parent == self.state / 'backups':
                backup_writes.append(path)
                if len(backup_writes) == 2:
                    raise OSError('simulated backup disk failure')
            original_atomic(path, raw, *args)

        with patch.object(release, 'atomic', side_effect=fail_second_backup):
            with self.assertRaisesRegex(OSError, 'backup disk failure'):
                release.install(**self.args)
        self.assertEqual(len(backup_writes), 2)
        self.assertTrue(backup_writes[0].is_file())
        self.assertFalse((self.state / 'journal.json').exists())
        state_before = self.tree(self.state)
        diagnostic = ('State preparation interrupted before journal; '
                      'no target files or SQL were changed; '
                      'remove only this incomplete state directory or choose a fresh --state')

        with patch.object(release, 'Database') as database:
            for function, extra in ((release.install, {}), (release.rollback, {'recovery': True})):
                with self.subTest(api=function.__name__):
                    with self.assertRaisesRegex(ValueError, diagnostic):
                        function(**self.args, **extra)
            for command in ('install', 'recover'):
                argv = ['crypt_release.py', command, '--bundle', str(self.bundle),
                        '--data-dir', str(self.data), '--state', str(self.state),
                        '--database', self.args['database'], '--client', str(self.client), '--offline']
                stderr = io.StringIO()
                with self.subTest(cli=command), patch.object(release.sys, 'argv', argv):
                    with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as exc:
                        release.main()
                    self.assertEqual(exc.exception.code, 1)
                    self.assertIn(diagnostic, stderr.getvalue())
            database.assert_not_called()
        self.assertEqual(self.tree(self.data), self.original)
        self.assertEqual(self.tree(self.client), client_before)
        self.assertEqual(self.tree(self.state), state_before)
        self.assertEqual(self.db.rows, [])
        self.assertEqual(self.db.transactions, 0)

    def test_backup_tampering_refused_before_writes(self):
        release.install(**self.args)
        journal = json.loads((self.state / 'journal.json').read_text())
        item = next(r for r in journal['files'] if r['before'] is not None)
        (self.state / item['backup']).write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'backup changed'):
            release.rollback(**self.args)
        self.assertEqual(self.db.transactions, 1)

    def test_bundle_corruption_and_extra_file(self):
        self.assertEqual(release.verify(self.bundle)['status'], 'PASS')
        put(self.bundle, 'unlisted', b'extra')
        with self.assertRaisesRegex(ValueError, 'Unexpected/missing'):
            release.verify(self.bundle)
        (self.bundle / 'unlisted').unlink()
        put(self.bundle, 'client/Data/patch-T.MPQ', b'damaged')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            release.verify(self.bundle)

    def test_archive_determinism_and_roundtrip(self):
        first, second = self.root / 'first.tar', self.root / 'second.tar'
        a = release.archive(self.bundle, first)
        b = release.archive(self.bundle, second)
        self.assertEqual(a['archive_sha256'], b['archive_sha256'])
        with tarfile.open(first) as archive:
            self.assertEqual(set(archive.getnames()), set(self.tree(self.bundle)))
            for member in archive:
                self.assertEqual(member.uid, 0)
                self.assertEqual(member.gid, 0)
                self.assertEqual(member.mtime, 0)
                self.assertEqual(archive.extractfile(member).read(),
                                 (self.bundle / member.name).read_bytes())
        with self.assertRaisesRegex(ValueError, 'fresh'):
            release.archive(self.bundle, first)

    def test_symlink_target_refused(self):
        (self.data / 'dbc/Map.dbc').unlink()
        (self.data / 'dbc/Map.dbc').symlink_to(self.bundle / 'server/dbc/Map.dbc')
        self.assert_preflight_refusal()

    def test_wrong_target_identity_refused(self):
        release.install(**self.args)
        self.args['database'] = 'different_database'
        with self.assertRaisesRegex(ValueError, 'different bundle/target'):
            release.rollback(**self.args)

    def test_wrong_mysql_server_refused(self):
        release.install(**self.args)
        self.db.uuid = '00000000-0000-0000-0000-000000000002'
        with self.assertRaisesRegex(ValueError, 'different bundle/target'):
            release.rollback(**self.args)
        self.assertEqual(self.db.transactions, 1)


class FormatTests(unittest.TestCase):
    def test_modelspawn_physical_names_and_bounds(self):
        def spawn(name, flags):
            return (struct.pack('<IHI7f', flags, 0, 1, *([0.] * 6), 1.) +
                    (bytes(24) if flags & 4 else b'') + struct.pack('<I', len(name)) + name + bytes(4))
        raw = b'VMAP_4.8' + struct.pack('<I', 2) + spawn(b'flower.m2\0', 1) + spawn(b'Tw800Crypt.wmo', 4)
        self.assertEqual(tile_models(raw), {'flower.m2', 'Tw800Crypt.wmo.vmo'})
        for broken in (raw[:-1], raw + b'X', b'VMAP_4.7' + raw[8:]):
            with self.assertRaises(ValueError):
                tile_models(broken)

    def test_current_binary_versions(self):
        binary_check('800.map', b'MAPS' + struct.pack('<II', 9, 12340))
        with self.assertRaises(ValueError):
            binary_check('800.map', b'MAPS' + struct.pack('<II', 8, 12340))
        tile = struct.pack('<4I', 0x4d4d4150, 7, 20, 8) + bytes(40) + struct.pack('<II', 0x444e4156, 7)
        binary_check('800.mmtile', tile)
        with self.assertRaises(ValueError):
            binary_check('800.mmtile', tile[:-1])

    def test_canonical_compilation_and_pin(self):
        sql = {n: (release.ROOT / 'data/sql/custom/db_world' / n).read_bytes() for n in SQL_HASHES}
        compiled = compile_sql(sql)
        self.assertEqual(len(compiled), 10)
        self.assertTrue(all('WHERE NOT EXISTS' not in stmt and 'PROCEDURE' not in stmt
                            and 'acore_world' not in stmt for _, _, stmt in compiled))
        sql['turtle_wow_maps.sql'] += b'\n'
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            compile_sql(sql)

    def test_identifier_injection_rejected(self):
        for bad in ('world;DROP DATABASE x', 'a`b', '../world', '', 'a' * 65, 'world-db'):
            with self.assertRaises(ValueError):
                identifier(bad)
        self.assertEqual(identifier('acore_crypt_release_test'), 'acore_crypt_release_test')

    def test_mysql_never_force_and_extra_file_first(self):
        db = Database('fixture', 'azeroth-dev', '/private/options.cnf')
        self.assertEqual(db.command[1], '--defaults-extra-file=/private/options.cnf')
        self.assertNotIn('--force', db.command)


if __name__ == '__main__':
    unittest.main()
