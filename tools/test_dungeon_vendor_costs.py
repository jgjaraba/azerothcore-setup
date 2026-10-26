#!/usr/bin/env python3
"""Dungeon cost contract + real private MySQL regression tests; no DEV access.

Run: python3 tools/test_dungeon_vendor_costs.py -v
Uses the existing Forest Troll mysql helpers and system mysql/mysqld. The
self-contained fixture reproduces the supported 16-column InnoDB overlay schema.
"""
import hashlib
import os
from pathlib import Path
import pwd
import re
import shutil
import struct
import subprocess
import tempfile
import time
import unittest

import test_forest_troll_sql as mysql_fixture


ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / 'data/sql/custom/db_world'
APPLY = SQL_DIR / 'dungeon_gear_vendor_cost.sql'
PROCEDURE = 'azerothcore_setup_dungeon_vendor_costs'
COLUMNS = ('ID', 'HonorPoints', 'ArenaPoints', 'ArenaBracket',
           *(f'ItemID_{n}' for n in range(1, 6)),
           *(f'ItemCount_{n}' for n in range(1, 6)),
           'RequiredArenaRating', 'ItemPurchaseGroup')
FIELDS = ', '.join(f'`{c}`' for c in COLUMNS)
IDS = {base + n for base in (97000, 98000, 99000) for n in range(10, 36)}
FOREIGN = (42, 7, 8, 9, 123, 456, 0, 0, 0, 12, 13, 0, 0, 0, 14, 15)


def numeric_rows(text):
    return [tuple(map(int, row.split(',')))
            for row in re.findall(r'^\s*\(([\d,\s]+)\)[,;]', text, re.M)]


def expected_rows():
    return numeric_rows(APPLY.read_text())


def insert(rows):
    return ('INSERT INTO itemextendedcost_dbc (' + FIELDS + ') VALUES '
            + ','.join('(' + ','.join(map(str, row)) + ')' for row in rows) + ';')


class StaticContract(unittest.TestCase):
    def test_all_78_full_numeric_records_match_tracked_binary(self):
        data = (ROOT / 'dbc/ItemExtendedCost.dbc').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         '24bc323061283e6c4c94a411318496720230ec83fe7315c1798ba8c0e280c4be')
        magic, count, fields, size, strings = struct.unpack_from('<4s4I', data)
        self.assertEqual((magic, count, fields, size, strings), (b'WDBC', 1070, 16, 64, 1))
        self.assertEqual(len(data), 20 + count * size + strings)
        binary = [row for row in struct.iter_unpack('<16I', data[20:20 + count * size])
                  if row[0] in IDS]
        rows = expected_rows()
        self.assertEqual(len(rows), 78)
        self.assertEqual({r[0] for r in rows}, IDS)
        self.assertEqual(sorted(rows), sorted(binary))  # Includes ItemPurchaseGroup.
        for row in rows:
            price = {97: 2, 98: 5, 99: 10}[row[0] // 1000]
            self.assertEqual(row, (row[0], 0, 0, 0, 90000 + row[0] % 1000,
                                   0, 0, 0, 0, price, 0, 0, 0, 0, 0, 0))
        # Both INSERTs must name every actual schema column explicitly.
        inserts = re.findall(r'INSERT INTO `(?:dungeon_vendor_costs_expected|itemextendedcost_dbc)`'
                             r'\s*\(([^)]+)\)', APPLY.read_text())
        self.assertEqual(len(inserts), 2)
        for columns in inserts:
            self.assertEqual(tuple(re.findall(r'`(\w+)`', columns)), COLUMNS)

    def test_manifest_dependency_order_and_complete_inventory(self):
        manifest = (SQL_DIR / 'manifest.txt').read_text().splitlines()
        start = manifest.index('dungeon_gear_vendor.sql')
        self.assertEqual(manifest[start:start + 5], [
            'dungeon_gear_vendor.sql', APPLY.name, 'dungeon_gear_vendor_npc.sql',
            'dungeon_gear_vendor_item.sql', 'dungeon_gear_vendor_loot.sql'])
        self.assertEqual(len(manifest), len(set(manifest)))
        self.assertEqual(set(manifest), {p.name for p in SQL_DIR.glob('*.sql')})
        result = mysql_fixture.execute(['bash', ROOT / 'scripts/apply-db-world.sh', '--validate'])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_all_928_catalog_entries_and_27_cost_references_covered(self):
        catalog = (SQL_DIR / 'dungeon_gear_vendor_item.sql').read_text()
        values = catalog.split('INSERT INTO `npc_vendor`', 1)[1].split('VALUES', 1)[1]
        rows = numeric_rows(values)
        self.assertEqual(len(rows), 928)
        self.assertTrue(all(len(row) == 7 for row in rows))
        self.assertEqual({row[0] for row in rows}, set(range(90300, 90326)))
        self.assertEqual(len({(r[0], r[1]) for r in rows}), 928)
        refs = {row[5] for row in rows}
        self.assertEqual(refs, set(range(97010, 97036)) | {99035})
        costs = {row[0]: row for row in expected_rows()}
        self.assertTrue(refs <= costs.keys())
        ordinary = [row for row in rows if row[2] != 13335]
        self.assertEqual(len(ordinary), 927)
        for row in ordinary:
            self.assertEqual(row[5], 97010 + row[0] - 90300)
            self.assertEqual((costs[row[5]][4], costs[row[5]][9]),
                             (90010 + row[0] - 90300, 2))
        mount, = [row for row in rows if row[2] == 13335]
        self.assertEqual((mount[0], mount[5]), (90325, 99035))
        self.assertEqual((costs[mount[5]][4], costs[mount[5]][9]), (90035, 10))


class PrivateMySQL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='dvc-mysql-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output = Path(cls.temp.name)
        datadir = cls.output / 'mysql'
        datadir.mkdir()
        socket = cls.output / 'm.sock'
        common = ['/usr/sbin/mysqld', '--no-defaults', '--datadir=' + str(datadir),
                  '--user=' + pwd.getpwuid(os.getuid()).pw_name,
                  '--innodb-buffer-pool-size=32M', '--innodb-redo-log-capacity=8M']
        mysql_fixture.checked([*common, '--initialize-insecure'])
        process = subprocess.Popen([
            *common, '--skip-networking', '--mysqlx=OFF', '--socket=' + str(socket),
            '--pid-file=' + str(cls.output / 'mysql.pid'),
            '--log-error=' + str(cls.output / 'mysql.log')],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        def stop():
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        cls.addClassCleanup(stop)
        cls.db = mysql_fixture.Fixture(socket, cls.output)
        for _ in range(120):
            if mysql_fixture.execute(cls.db.command[:-1], input='SELECT 1;', env=cls.db.env).returncode == 0:
                break
            mysql_fixture.require(process.poll() is None, 'Private mysqld stopped')
            time.sleep(.5)
        else:
            raise RuntimeError('Private mysqld startup timed out')
        mysql_fixture.checked(cls.db.command[:-1], input='CREATE DATABASE acore_world;', env=cls.db.env)
        mysql_fixture.require(cls.db.query('SELECT @@skip_networking;').strip() == '1', 'Networking enabled')
        mysql_fixture.require(Path(cls.db.query('SELECT @@datadir;').strip()).resolve() == datadir,
                              'Wrong private datadir')
        mysql_fixture.require(cls.db.query('SELECT @@socket;').strip() == str(socket), 'Wrong socket')
        mysql_fixture.require(cls.db.query("SHOW VARIABLES LIKE 'mysqlx_port';").strip() == '', 'mysqlx enabled')
        mysql_fixture.require('--force' not in cls.db.command, '--force is forbidden')

    def setUp(self):
        self.db.query(f'DROP PROCEDURE IF EXISTS `{PROCEDURE}`;'
                      'DROP TABLE IF EXISTS itemextendedcost_dbc;'
                      'DROP TABLE IF EXISTS installer_progress;'
                      'CREATE TABLE itemextendedcost_dbc ('
                      + ','.join(f'`{c}` INT NOT NULL DEFAULT 0' for c in COLUMNS)
                      + ', PRIMARY KEY (`ID`)) ENGINE=InnoDB;'
                      + insert([FOREIGN]))

    def snapshot(self):
        return [tuple(map(int, line.split('\t'))) for line in
                self.db.query(f'SELECT {FIELDS} FROM itemextendedcost_dbc ORDER BY ID;').splitlines()]

    def run_sql(self, error=None):
        before = self.snapshot()
        result = mysql_fixture.execute(self.db.command, input=APPLY.read_text(), env=self.db.env)
        if error is None:
            self.assertEqual(result.returncode, 0, result.stderr)
            routines = self.db.query("SELECT COUNT(*) FROM information_schema.ROUTINES "
                                     "WHERE ROUTINE_SCHEMA='acore_world';").strip()
            self.assertEqual(routines, '0')
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(error, result.stderr)
            self.assertEqual(self.snapshot(), before)
        return result

    def test_apply_twice_preserves_foreign_and_retains_exact_existing(self):
        rows = expected_rows()
        # Identical semantics at a foreign ID must also be preserved.
        foreign_copy = (43, *rows[0][1:])
        self.db.query(insert([rows[0], rows[-1], foreign_copy]))
        # Exact existing rows must not be deleted/reinserted or updated.
        for event in ('UPDATE', 'DELETE'):
            self.db.query(f'CREATE TRIGGER reject_{event.lower()} BEFORE {event} ON itemextendedcost_dbc '
                          "FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='existing row rewritten';")
        wanted = sorted([FOREIGN, foreign_copy, *rows])
        self.run_sql()
        self.assertEqual(self.snapshot(), wanted)
        self.run_sql()
        self.assertEqual(self.snapshot(), wanted)

    def test_every_non_id_column_conflict_refuses_before_any_insert(self):
        rows = expected_rows()
        for index in range(1, 16):
            with self.subTest(column=COLUMNS[index]):
                self.setUp()
                conflict = list(rows[-1])
                conflict[index] += 1
                self.db.query(insert([rows[0], tuple(conflict)]))
                self.run_sql('owned ID has different fields; no overlay rows changed')
                self.assertEqual(self.snapshot(), sorted([FOREIGN, rows[0], tuple(conflict)]))

    def test_failed_routine_is_fail_safe_on_retry(self):
        conflict = list(expected_rows()[-1])
        conflict[-1] = 1
        self.db.query(insert([conflict]))
        self.run_sql('owned ID has different fields')
        self.db.query(f'DELETE FROM itemextendedcost_dbc WHERE ID={conflict[0]};')
        self.run_sql('already exists')  # No automatic DROP of failed routine.
        self.db.query(f'DROP PROCEDURE `{PROCEDURE}`;')
        self.run_sql()
        self.assertEqual(self.snapshot(), sorted([FOREIGN, *expected_rows()]))

    def test_mid_insert_failure_rolls_back_all_rows(self):
        self.db.query('DELIMITER $$\nCREATE TRIGGER reject_insert BEFORE INSERT ON itemextendedcost_dbc '
                      'FOR EACH ROW BEGIN IF NEW.ID=98010 THEN '
                      "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='fixture insert failure'; END IF; END$$\nDELIMITER ;\n")
        self.run_sql('fixture insert failure')
        self.assertEqual(self.snapshot(), [FOREIGN])

    def test_nontransactional_engine_refused_without_changes(self):
        self.db.query('ALTER TABLE itemextendedcost_dbc ENGINE=MyISAM;')
        self.run_sql('itemextendedcost_dbc must be InnoDB')
        self.assertEqual(self.db.query("SELECT ENGINE FROM information_schema.TABLES "
                                       "WHERE TABLE_SCHEMA='acore_world' AND TABLE_NAME='itemextendedcost_dbc';").strip(),
                         'MyISAM')

    def test_real_installer_stops_before_npc_and_inventory_on_partial_conflict(self):
        self.db.query('CREATE TABLE installer_progress (step INT PRIMARY KEY) ENGINE=InnoDB;')
        rows = expected_rows()
        conflict = list(rows[-1])
        conflict[9] = 11
        self.db.query(insert([rows[0], conflict]))
        before = self.snapshot()
        with tempfile.TemporaryDirectory(prefix='dvc-installer-') as temp:
            fixture = Path(temp)
            sql_dir = fixture / 'sql'
            sql_dir.mkdir()
            bin_dir = fixture / 'bin'
            bin_dir.mkdir()
            # Follow actual manifest order; stub unrelated currency/NPC/stock SQL.
            manifest = (SQL_DIR / 'manifest.txt').read_text().splitlines()
            start = manifest.index('dungeon_gear_vendor.sql')
            names = manifest[start:start + 4]
            (sql_dir / 'manifest.txt').write_text('\n'.join(names) + '\n')
            for name, text in zip(names, ['SELECT 1;', APPLY.read_text(),
                                          'INSERT INTO installer_progress VALUES (1);',
                                          'INSERT INTO installer_progress VALUES (2);']):
                (sql_dir / name).write_text(text)
            # Discard installer login-path arguments; invoke only the isolated
            # --no-defaults/socket client. Never create or read a host login path.
            wrapper = bin_dir / 'mysql'
            private_command = [shutil.which('mysql'), *self.db.command[1:]]
            wrapper.write_text('#!/usr/bin/env python3\nimport os\n'
                               + f'os.execv({private_command[0]!r}, {private_command!r})\n')
            wrapper.chmod(0o755)
            env = dict(self.db.env, PATH=str(bin_dir) + os.pathsep + os.environ['PATH'],
                       SQL_DIR=str(sql_dir), MANIFEST=str(sql_dir / 'manifest.txt'),
                       LOGIN_PATH='unused-private-fixture')
            result = mysql_fixture.execute(['bash', ROOT / 'scripts/apply-db-world.sh'], env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('owned ID has different fields', result.stderr)
            self.assertNotIn('Applying: dungeon_gear_vendor_npc.sql', result.stdout)
            self.assertNotIn('Applying: dungeon_gear_vendor_item.sql', result.stdout)
            self.assertEqual(self.db.query('SELECT COUNT(*) FROM installer_progress;').strip(), '0')
            self.assertEqual(self.snapshot(), before)
            # Recover the fixture and prove this same installer can reach both
            # subsequent files on a valid apply, including a second apply.
            self.db.query(f'DROP PROCEDURE `{PROCEDURE}`;'
                          f'DELETE FROM itemextendedcost_dbc WHERE ID={conflict[0]};')
            for _ in range(2):
                self.db.query('DELETE FROM installer_progress;')
                result = mysql_fixture.execute(['bash', ROOT / 'scripts/apply-db-world.sh'], env=env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(self.db.query('SELECT step FROM installer_progress ORDER BY step;'), '1\n2\n')
                self.assertEqual(self.snapshot(), sorted([FOREIGN, *rows]))


if __name__ == '__main__':
    unittest.main()
