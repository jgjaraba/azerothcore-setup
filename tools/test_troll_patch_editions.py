"""Independent edition/SQL checks. Integration uses pinned original MPQs;
TROLL_EDITIONS_INTEGRATION=1 and TROLL_EDITIONS_MYSQL=1 enable the full fixtures.
MySQL is private and network-disabled; reference clients/DEV are never written.
"""
import json
import io
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
from PIL import Image

import build_troll_patch_editions as editions
import test_forest_troll_sql as fixture


def independent_decode(raw, level):
    width, height = struct.unpack_from('<2I', raw, 12)
    width, height = max(1, width >> level), max(1, height >> level)
    offset = struct.unpack_from('<I', raw, 20 + level * 4)[0]
    count = width * height
    if raw[8] == 2:
        # Feed each DXT mip separately to Pillow's independent BC decoder.
        size = struct.unpack_from('<I', raw, 84 + level * 4)[0]
        header = bytearray(raw[:148])
        struct.pack_into('<2I', header, 12, width, height)
        struct.pack_into('<16I', header, 20, 1172, *([0] * 15))
        struct.pack_into('<16I', header, 84, size, *([0] * 15))
        return np.asarray(Image.open(io.BytesIO(bytes(header) + bytes(1024) + raw[offset:offset + size])).convert('RGBA'))
    if raw[8] == 3:
        return np.frombuffer(raw, np.uint8, count * 4, offset).reshape(height, width, 4)[:, :, [2, 1, 0, 3]]
    palette = np.frombuffer(raw, np.uint8, 1024, 148).reshape(256, 4)
    indices = np.frombuffer(raw, np.uint8, count, offset)
    rgb = palette[indices][:, [2, 1, 0]]
    depth = raw[9]
    if depth == 0:
        alpha = np.full(count, 255, np.uint8)
    else:
        packed = np.frombuffer(raw, np.uint8, (count * depth + 7) // 8, offset + count)
        i = np.arange(count)
        alpha = ((packed[i // (8 // depth)] >> ((i % (8 // depth)) * depth))
                 & ((1 << depth) - 1)) * (255 // ((1 << depth) - 1))
    return np.column_stack((rgb, alpha)).reshape(height, width, 4)


class ContractTests(unittest.TestCase):
    def test_output_protections_precede_source_reads(self):
        for output in (editions.ROOT / editions.PACKAGE / 'fresh', Path('/home/dev/wow-335/fresh'),
                       Path('/home/dev/wow-turtle/fresh')):
            with self.assertRaisesRegex(ValueError, 'overlaps'):
                editions.build(output)


@unittest.skipUnless(os.environ.get('TROLL_EDITIONS_INTEGRATION') == '1', 'Pinned sources opt-in')
class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='troll-editions-test-', dir=editions.ROOT / 'work')
        cls.work = Path(cls.temp.name)
        cls.first, cls.second = cls.work / 'first', cls.work / 'second'
        cls.reports = editions.build(cls.first)
        cls.repeat = editions.build(cls.second)
        cls.base = editions.base_path()
        cls.legacy_report = editions.verify_base(cls.base)
        cls.original = {n: raw for n, raw in editions.members(editions.legacy.forest.MPQ, cls.base / editions.PRODUCTS[0]).values()}
        _, skins, _ = editions.split_rows(cls.legacy_report)
        cls.retired = [r for r in skins if r[2] == 0 and r[9] in (33, 34, 35)]
        cls.active = [r for r in skins if r not in cls.retired]
        # Reconstruct the exact previous MPQ in scratch, independent of current publication.
        cls.old_payload = dict(cls.original)
        for name in sorted({n for r in skins if r[3] == 1 for n in r[4:6]}):
            cls.old_payload[name], _ = editions.palette_encode(cls.original[name], allow_quantize=True)
        old_patch = cls.work / 'old-optional.MPQ'
        editions.legacy.create_mpq(old_patch, cls.old_payload, cls.work)
        assert editions.sha(old_patch) == editions.OLD_PUBLICATIONS['optional-extra-skins'][editions.PRODUCTS[0]]

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_two_source_builds_all_files_identical(self):
        first = {p.relative_to(self.first): p.read_bytes() for p in self.first.rglob('*') if p.is_file()}
        second = {p.relative_to(self.second): p.read_bytes() for p in self.second.rglob('*') if p.is_file()}
        self.assertEqual(first, second)
        current = self.work / 'from-current'
        actual_sha = editions.sha
        old_optional = editions.ROOT / editions.PACKAGE / 'optional-extra-skins' / editions.PRODUCTS[0]
        # Exercise post-upgrade builds: old a09 is unavailable, pinned remaining
        # payload fingerprint must still be checked; never convert retired faces.
        with patch.object(editions, 'sha', side_effect=lambda p: editions.PUBLICATIONS['optional-extra-skins'][editions.PRODUCTS[0]]
                          if Path(p) == old_optional else actual_sha(p)), \
             patch.object(editions, 'palette_encode', wraps=editions.palette_encode) as convert:
            editions.build(current, 'current')
            self.assertEqual(convert.call_count, 36)
            retired_faces = {self.original[n] for r in self.retired if r[3] == 1 for n in r[4:6]}
            self.assertFalse(any(call.args[0] in retired_faces for call in convert.call_args_list))
        self.assertEqual(first, {p.relative_to(current): p.read_bytes() for p in current.rglob('*') if p.is_file()})

    def test_all_payloads_record_bytes_pixels_and_accepted_pair(self):
        primary_rows, skins, forest = editions.split_rows(self.legacy_report)
        removed = {n for r in skins for n in r[4:7] if n}
        retired_members = {n for r in self.retired for n in r[4:7] if n} - {n for r in self.active for n in r[4:7] if n}
        faces = {n for r in self.active if r[3] == 1 for n in r[4:6]}
        self.assertEqual(len(removed), 93)
        self.assertEqual((len(self.retired), len(retired_members), len(faces)), (21, 12, 36))
        before_rows, before_strings = editions.legacy.forest.read_dbc(self.original[editions.SECTIONS])
        for edition, count in (('primary', 213), ('optional-extra-skins', 294)):
            report = self.reports[edition]
            payload = {n: raw for n, raw in editions.members(editions.legacy.forest.MPQ,
                       self.first / edition / editions.PRODUCTS[0]).values()}
            self.assertEqual(len(payload), count)
            self.assertEqual(set(payload), set(self.original) - (removed if edition == 'primary' else retired_members))
            rows, strings = editions.legacy.forest.read_dbc(payload[editions.SECTIONS])
            self.assertEqual(strings, before_strings)
            ids = {r[0] for r in (skins if edition == 'primary' else self.retired)}
            self.assertEqual(rows, [r for r in before_rows if r[0] not in ids])
            self.assertFalse(any(r[1] == 8 and r[2] == 0 and r[3] in (0, 1, 4) and r[9] in (33, 34, 35) for r in rows))
            if edition == 'primary':
                self.assertFalse(any(r[1] == 8 and r[3] in (0, 1, 4) and r[9] >= 24 for r in rows))
            changes = {c['member']: c for c in report['face_conversions']}
            for name, raw in payload.items():
                original = self.original[name]
                if name == editions.SECTIONS:
                    continue
                if edition != 'primary':
                    self.assertEqual(raw, self.old_payload[name], name)
                if name not in changes:
                    self.assertEqual(raw, original, name)
                if name.lower().endswith('.blp'):
                    info = editions.legacy.forest.validate_blp(raw)
                    for level in range(len(info['mips'])):
                        before, after = independent_decode(original, level), independent_decode(raw, level)
                        np.testing.assert_array_equal(before[:, :, 3], after[:, :, 3], err_msg=name)
                        if name not in changes or (level == 0 and not changes[name]['quantized']):
                            np.testing.assert_array_equal(before, after, err_msg=name)
                        if name in changes:
                            self.assertEqual(raw[8], 1)
                            self.assertEqual(raw[10], 8)
                            self.assertEqual(struct.unpack_from('<I', raw, 20)[0], 1172)
                            error = np.abs(after[:, :, :3].astype(np.int16) - before[:, :, :3].astype(np.int16))
                            measured = changes[name]['mip_errors'][level]
                            self.assertEqual(float(error.mean()), measured['rgb_mae'])
                            self.assertEqual(int(error.max()), measured['rgb_max'])
                            if 'rgb_p99' in measured:
                                self.assertEqual(float(np.quantile(error, .99)), measured['rgb_p99'])
            if edition != 'primary':
                self.assertEqual(set(changes), faces)
                self.assertEqual(sum(c['quantized'] for c in changes.values()), 0)
                self.assertEqual({r[9] for r in rows if tuple(r[1:4]) == (8, 1, 0) and r[9] >= 24}, set(range(24, 33)))
                self.assertEqual({r[9] for r in rows if tuple(r[1:4]) == (8, 0, 0) and r[9] >= 24}, set(range(24, 33)))
            else:
                self.assertEqual(editions.sha(self.first / edition / editions.PRODUCTS[0]),
                                 editions.OLD_PUBLICATIONS['primary'][editions.PRODUCTS[0]])
            if edition != 'primary':
                trial = editions.members(editions.legacy.forest.MPQ,
                    editions.ROOT / editions.PACKAGE / 'face-format-test/Data/patch-S.MPQ')
                for name in faces:
                    if '\\Male\\100_Face' in name:
                        self.assertEqual(payload[name], trial[editions.key(name)][1])

    def test_publication_preflight_archive_idempotence_unknown_refusal(self):
        root = self.work / 'sandbox'
        package = root / editions.PACKAGE
        (package / 'Data').mkdir(parents=True)
        for name in editions.PRODUCTS:
            shutil.copyfile(self.base / name, package / name)
        for name, relative in editions.SQL_PATHS.items():
            if name.startswith('primary'):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((self.first / ('legacy-rollback.sql' if 'rollback' in name else 'legacy.sql')).read_bytes())
        snapshot = lambda: {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
        blocker = root / 'data/sql/optional'
        blocker.write_bytes(b'foreign regular file in directory position')
        before = snapshot()
        with patch.object(editions.shutil, 'copyfile', wraps=shutil.copyfile) as copy:
            with self.assertRaisesRegex(ValueError, 'Non-directory destination ancestor'):
                editions.publish(self.first, root)
            copy.assert_not_called()
        self.assertEqual(before, snapshot())
        blocker.unlink()
        staging = root / editions.SQL_PATHS['optional-rollback.sql']
        staging = staging.with_name(staging.name + '.tmp')
        staging.parent.mkdir(parents=True, exist_ok=True)
        staging.write_bytes(b'foreign staging')
        before = snapshot()
        with patch.object(editions.shutil, 'copyfile', wraps=shutil.copyfile) as copy:
            with self.assertRaisesRegex(ValueError, 'Stale'):
                editions.publish(self.first, root)
            copy.assert_not_called()
        self.assertEqual(before, snapshot())
        staging.unlink()
        editions.publish(self.first, root)
        after = snapshot()
        editions.publish(self.second, root)
        self.assertEqual(after, snapshot())
        editions.verify_base(package / 'v2')
        for edition, target in (('primary', package), ('optional-extra-skins', package / 'optional-extra-skins')):
            path = target / 'report.json'
            original = path.read_bytes()
            value = json.loads(original)
            value['unknown'] = True
            editions.write_json(path, value)
            editions.checksum(target)
            bad = snapshot()
            with self.assertRaisesRegex(ValueError, 'unknown current'):
                editions.publish(self.first, root)
            self.assertEqual(bad, snapshot())
            path.write_bytes(original)
            editions.checksum(target)

    def test_exact_previous_edition_upgrade_when_available(self):
        package = editions.ROOT / editions.PACKAGE
        candidates = [dict(primary=package, **{'optional-extra-skins': package / 'optional-extra-skins'}),
                      {e: editions.ROOT / 'work/troll-editions-v3-final' / e for e in editions.OLD_PUBLICATIONS}]
        previous = next((paths for paths in candidates if all(
            all((paths[e] / n).is_file() and editions.sha(paths[e] / n) == h for n, h in pins.items())
            for e, pins in editions.OLD_PUBLICATIONS.items())), None)
        if previous is None:
            self.skipTest('Exact previous report/MPQ/checksum triple unavailable')
        root = self.work / 'old-upgrade'
        for e, source in previous.items():
            target = root / editions.PACKAGE / ('' if e == 'primary' else e)
            for n in editions.PRODUCTS:
                (target / n).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source / n, target / n)
        for n in editions.PRODUCTS:
            target = root / editions.PACKAGE / 'v2' / n
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.base / n, target)
        main, skins, forest = editions.split_rows(self.legacy_report)
        for name, rollback in (('optional.sql', False), ('optional-rollback.sql', True)):
            target = root / editions.SQL_PATHS[name]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(editions.render_sql(skins, 'optional', rollback,
                                                 prerequisites=() if rollback else forest + main))
        editions.publish(self.first, root)
        for e in editions.PUBLICATIONS:
            target = root / editions.PACKAGE / ('' if e == 'primary' else e)
            editions.legacy.verify_publication(target, editions.PUBLICATIONS[e])

    @unittest.skipUnless(os.environ.get('TROLL_EDITIONS_MYSQL') == '1', 'Private MySQL opt-in')
    def test_private_mysql_profiles_legacy_upgrade_conflicts_and_modes(self):
        with tempfile.TemporaryDirectory(prefix='te-mysql-') as short:
            output = self.work / 'mysql-fixture'
            output.mkdir()
            datadir = output / 'data'
            datadir.mkdir()
            socket = Path(short) / 'm.sock'
            common = ['/usr/sbin/mysqld', '--no-defaults', '--datadir=' + str(datadir),
                      '--user=' + pwd.getpwuid(os.getuid()).pw_name,
                      '--innodb-buffer-pool-size=32M', '--innodb-redo-log-capacity=8M']
            fixture.checked([*common, '--initialize-insecure'])
            process = subprocess.Popen([*common, '--skip-networking', '--mysqlx=OFF',
                '--socket=' + str(socket), '--pid-file=' + str(output / 'mysql.pid'),
                '--log-error=' + str(output / 'mysql.log')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
                ddl = 'CREATE TABLE charsections_dbc (' + ','.join(
                    f'`{c}` ' + ('VARCHAR(100) NOT NULL' if c.startswith('Texture') else 'INT UNSIGNED NOT NULL')
                    for c in fixture.COLUMNS) + ', PRIMARY KEY (`Id`)) ENGINE=MyISAM;'
                main, skins, forest = editions.split_rows(self.legacy_report)
                active, retired = self.active, self.retired
                for mode in ('STRICT_TRANS_TABLES', 'STRICT_TRANS_TABLES,NO_BACKSLASH_ESCAPES'):
                    db.reset(ddl)
                    def run(name, error=None):
                        primary = name.startswith('primary')
                        proc = 'azerothcore_setup_' + ('troll_primary' if primary else 'troll_extra_skins')
                        rollback = self.first / (('primary' if primary else 'optional') + '-rollback.sql')
                        with patch.multiple(fixture, PROCEDURE=proc, ROLLBACK=rollback):
                            db.canonical(self.first / name, mode, name, error, engine_after='InnoDB')
                    run('optional.sql', 'require exact')
                    db.query(fixture.insert(forest + main + skins))  # legacy454 + unrelated sentinel
                    run('primary.sql')  # reapply does not implicitly undo opt-in
                    self.assertEqual(db.snapshot(), sorted([fixture.SENTINEL] + forest + main + skins))
                    run('primary-rollback.sql', 'Remove optional')
                    run('optional.sql')  # Upgrade installed156 -> current135, in one transaction.
                    self.assertEqual(db.snapshot(), sorted([fixture.SENTINEL] + forest + main + active))
                    for name in ('optional-rollback.sql', 'optional-rollback.sql', 'primary.sql', 'primary.sql'):
                        run(name)
                        self.assertEqual(db.snapshot(), sorted([fixture.SENTINEL] + forest + main))
                    for name in ('optional.sql', 'optional.sql'):
                        run(name)
                        self.assertEqual(db.snapshot(), sorted([fixture.SENTINEL] + forest + main + active))
                    run('optional-rollback.sql')
                    # A foreign retired ID/case/tuple must abort the entire cleanup+insert.
                    for col, value in ((7, retired[0][7] ^ 1), (4, retired[0][4].swapcase()), (0, 30002)):
                        foreign = retired[0].copy()
                        foreign[col] = value
                        db.query(fixture.insert(retired[1:] + [foreign]))
                        for name in ('optional.sql', 'optional-rollback.sql'):
                            run(name, 'semantic tuple occupied' if col == 0 else 'owned ID has different fields')
                        db.query('DELETE FROM charsections_dbc WHERE Id IN (' + ','.join(str(r[0]) for r in retired[1:] + [foreign]) + ');')
                    # Old156 rollback compatibility returns exactly principal298.
                    db.query(fixture.insert(skins))
                    run('optional-rollback.sql')
                    self.assertEqual(db.snapshot(), sorted([fixture.SENTINEL] + forest + main))
                    # Prerequisite is an exact all-field join, not a row count.
                    for row, col, value in ((forest[0], 4, forest[0][4].swapcase()),
                                            (main[0], 7, main[0][7] ^ 1),
                                            (forest[0], 5, forest[0][5] + ' ')):
                        db.query(f'UPDATE charsections_dbc SET `{fixture.COLUMNS[col]}`={fixture.literal(value)} WHERE Id={row[0]};')
                        run('optional.sql', 'require exact')
                        db.query(f'UPDATE charsections_dbc SET `{fixture.COLUMNS[col]}`={fixture.literal(row[col])} WHERE Id={row[0]};')
                    # Both profiles reject foreign IDs and semantic tuples.
                    for name, selected in (('primary', main), ('optional', skins)):
                        if name == 'primary':
                            run('primary-rollback.sql')
                        for conflict in ('id', 'tuple'):
                            foreign = selected[-1].copy()
                            foreign[7 if conflict == 'id' else 0] = 99 if conflict == 'id' else 30001
                            db.query(fixture.insert([foreign]))
                            for suffix in ('.sql', '-rollback.sql'):
                                run(name + suffix, 'owned ID has different fields' if conflict == 'id' else 'semantic tuple occupied')
                            db.query(f'DELETE FROM charsections_dbc WHERE Id={foreign[0]};')
                        if name == 'primary':
                            run('primary.sql')
                    run('primary-rollback.sql')
                    run('primary-rollback.sql')
                    self.assertEqual(db.snapshot(), sorted([fixture.SENTINEL] + forest))
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
