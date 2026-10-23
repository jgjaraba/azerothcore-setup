#!/usr/bin/env python3
"""Real MySQL fixture for the published ForestTroll SQL (no DEV writes).

Only SHOW CREATE TABLE is read from azeroth-dev. All other SQL goes to a fresh
private, network-disabled mysqld as insecure local root. Requires system mysql
and /usr/sbin/mysqld; no builder imports or proprietary inputs are needed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
APPLY = ROOT / 'data/sql/custom/db_world/turtle_forest_troll_skins.sql'
ROLLBACK = ROOT / 'data/sql/rollback/turtle_forest_troll_skins.sql'
_CLIENT = ROOT / 'client_patches/turtle_forest_troll'
PUBLISHED = (_CLIENT / 'v1/report.json' if (_CLIENT / 'v1/report.json').exists()
             else _CLIENT / 'report.json')
COLUMNS = ('Id', 'Race', 'Gender', 'GenType', 'TexturePath1', 'TexturePath2',
           'TexturePath3', 'Flags', 'Type', 'Color')
SENTINEL = [30000, 1, 0, 0, 'fixture\\unrelated.blp', '', '', 17, 0, 254]
PROCEDURE = 'azerothcore_setup_forest_troll_skins'


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def execute(command, **kwargs):
    return subprocess.run(list(map(str, command)), text=True, capture_output=True,
                          timeout=120, **kwargs)


def checked(command, **kwargs):
    result = execute(command, **kwargs)
    require(result.returncode == 0, f'{command[0]} failed: {result.stderr}')
    return result.stdout


def literal(value):
    # Independent fixture inserts also work in either backslash-escaping mode.
    if isinstance(value, str):
        return "CONVERT(X'" + value.encode('utf-8').hex() + "' USING utf8mb4)"
    return str(value)


def insert(rows):
    return ('INSERT INTO charsections_dbc (' + ','.join(f'`{c}`' for c in COLUMNS)
            + ') VALUES ' + ','.join('(' + ','.join(map(literal, r)) + ')'
                                    for r in rows) + ';')


class Fixture:
    def __init__(self, socket, output):
        self.command = ['mysql', '--no-defaults', '--user=root', '--protocol=SOCKET',
                        '--socket=' + str(socket), '--default-character-set=utf8mb4',
                        '--batch', '--raw', '--skip-column-names', 'acore_world']
        self.env = os.environ.copy()
        self.env['MYSQL_TEST_LOGIN_FILE'] = str(output / 'nonexistent-login-file')
        self.output = output
        self.runs = []

    def query(self, sql):
        return checked(self.command, input=sql, env=self.env)

    def engine(self):
        return self.query("SELECT ENGINE FROM information_schema.TABLES "
                          "WHERE TABLE_SCHEMA='acore_world' "
                          "AND TABLE_NAME='charsections_dbc';").strip()

    def reset(self, ddl):
        # Preserve live columns/indexes, but establish the migration baseline
        # explicitly on our private table even when DEV is already InnoDB.
        self.query('DROP TABLE IF EXISTS charsections_dbc;\n' + ddl
                   + 'ALTER TABLE charsections_dbc ENGINE=MyISAM;\n' + insert([SENTINEL]))
        require(self.engine() == 'MyISAM' and self.snapshot() == [SENTINEL],
                'Private reset must establish the MyISAM sentinel baseline')

    def snapshot(self):
        # Hex transports JSON without mysql CLI escaping or collation equality.
        fields = ','.join(f'`{c}`' for c in COLUMNS)
        result = self.query(f'SELECT HEX(CAST(JSON_ARRAY({fields}) AS CHAR)) '
                            'FROM charsections_dbc ORDER BY Id;')
        return [json.loads(bytes.fromhex(line).decode('utf-8'))
                for line in result.splitlines()]

    def canonical(self, path, mode, label, error=None, engine_after=None):
        before = self.snapshot()
        engine_before = self.engine()
        # SET must be in the SAME client session, before CREATE PROCEDURE: MySQL
        # captures the session sql_mode when creating a stored routine.
        prefix = f'SET SESSION sql_mode={literal(mode)};\nSELECT @@SESSION.sql_mode;\n'
        result = execute(self.command, input=prefix + path.read_text(), env=self.env)
        number = len(self.runs) + 1
        log = f'{number:03d}-{label}.log'
        (self.output / log).write_text(result.stdout + result.stderr)
        record = dict(label=label, sql=path.relative_to(ROOT).as_posix(), mode=mode,
                      returncode=result.returncode, log=log,
                      engine_before=engine_before, engine_after=self.engine())
        self.runs.append(record)
        require(record['engine_after'] == (engine_after or engine_before),
                f'{label}: unexpected engine transition: {record}')
        observed = result.stdout.splitlines()[0]
        require(set(filter(None, observed.split(','))) == set(filter(None, mode.split(','))),
                f'{label}: session mode differs: {observed}')
        routine = PROCEDURE + ('_rollback' if path == ROLLBACK else '')
        if error is None:
            require(result.returncode == 0, f'{label}: {result.stderr}')
            require(self.query('SELECT COUNT(*) FROM information_schema.ROUTINES '
                               f"WHERE ROUTINE_SCHEMA='acore_world' AND ROUTINE_NAME='{routine}';").strip()
                    == '0', f'{label}: success left procedure behind')
        else:
            require(result.returncode != 0 and 'ERROR 1644 (45000)' in result.stderr
                    and error in result.stderr, f'{label}: wrong refusal: {result.stderr}')
            require(self.snapshot() == before, f'{label}: refusal changed rows')
            require(self.query('SELECT COUNT(*) FROM information_schema.ROUTINES '
                               f"WHERE ROUTINE_SCHEMA='acore_world' AND ROUTINE_NAME='{routine}';").strip()
                    == '1', f'{label}: expected failed procedure to remain')
            # mysql exits on CALL failure; temporary table vanishes with that
            # connection. Explicitly clean the persistent routine, private only.
            self.query(f'DROP PROCEDURE `{routine}`; '
                       'DROP TEMPORARY TABLE IF EXISTS forest_troll_skins_expected;')
            require(self.snapshot() == before, f'{label}: cleanup changed rows')
            record['expected_refusal'] = error


def suite(db, expected, mode, checks):
    tag = 'no-backslash' if 'NO_BACKSLASH_ESCAPES' in mode.split(',') else 'default'
    baseline = [SENTINEL]
    installed = sorted(baseline + expected)

    def state(wanted, label):
        require(db.snapshot() == sorted(wanted), f'{tag}/{label}: full row state differs')
        require(db.engine() == 'InnoDB', f'{tag}/{label}: engine must remain InnoDB')
        checks.append(f'{tag}/{label}')

    require(db.engine() == 'MyISAM', f'{tag}: expected fresh private MyISAM table')
    db.canonical(ROLLBACK, mode, tag + '-fresh-myisam-rollback', 'target must be InnoDB')
    require(db.snapshot() == baseline and db.engine() == 'MyISAM',
            f'{tag}: rollback altered fresh MyISAM baseline')
    checks.append(f'{tag}/fresh-myisam-rollback-refused-rows-and-engine-unchanged')
    for path, label, wanted in [(APPLY, 'apply-90', installed),
                                (APPLY, 'apply-repeat', installed),
                                (ROLLBACK, 'rollback-all-90', baseline),
                                (ROLLBACK, 'rollback-repeat-empty', baseline)]:
        db.canonical(path, mode, tag + '-' + label, engine_after='InnoDB')
        state(wanted, label)

    # Fresh migration with a foreign row occupying an owned ID. ALTER TABLE
    # precedes the row transaction: its engine change survives the later SIGNAL.
    collision = SENTINEL.copy()
    collision[0] = expected[-1][0]
    db.query(insert([collision]))
    db.query('ALTER TABLE charsections_dbc ENGINE=MyISAM;')
    require(db.engine() == 'MyISAM', f'{tag}: collision baseline must be MyISAM')
    for path in (APPLY, ROLLBACK):
        db.canonical(path, mode, tag + '-id-collision-' + path.parent.name,
                     'owned ID has different fields', engine_after='InnoDB')
    state(baseline + [collision], 'id-collision-preserved')
    checks.append(f'{tag}/non-atomic-migration-persists-after-collision-refusal')
    db.query(f'DELETE FROM charsections_dbc WHERE Id={collision[0]};')

    foreign = expected[-1].copy()
    foreign[0] = 30001
    db.query(insert([foreign]))
    for path in (APPLY, ROLLBACK):
        db.canonical(path, mode, tag + '-foreign-tuple-' + path.parent.name,
                     'semantic tuple occupied')
    state(baseline + [foreign], 'foreign-tuple-before-apply-preserved')
    db.query('DELETE FROM charsections_dbc WHERE Id=30001;')

    db.canonical(APPLY, mode, tag + '-reinstall')
    state(installed, 'reinstall-90')
    # Exercise every character column, including empty strings, and numeric
    # flags independently of the semantic key (which deliberately excludes Flags).
    original = expected[-1]
    mutations = [('flags', 7, original[7] ^ 1), ('tuple', 9, 253)]
    for index in (4, 5, 6):
        if original[index]:
            mutations.append((f'case-{index}', index, original[index].swapcase()))
        mutations.append((f'trailing-space-{index}', index, original[index] + ' '))
    for name, index, value in mutations:
        db.query(f'UPDATE charsections_dbc SET `{COLUMNS[index]}`={literal(value)} '
                 f'WHERE Id={original[0]};')
        changed = [r.copy() for r in installed]
        next(r for r in changed if r[0] == original[0])[index] = value
        state(changed, name + '-injected')
        for path in (APPLY, ROLLBACK):
            db.canonical(path, mode, tag + '-' + name + '-' + path.parent.name,
                         'owned ID has different fields')
        state(changed, name + '-preserved')
        db.query(f'UPDATE charsections_dbc SET `{COLUMNS[index]}`={literal(original[index])} '
                 f'WHERE Id={original[0]};')
        state(installed, name + '-restored')

    db.query(insert([foreign]))
    for path in (APPLY, ROLLBACK):
        db.canonical(path, mode, tag + '-installed-foreign-tuple-' + path.parent.name,
                     'semantic tuple occupied')
    state(installed + [foreign], 'installed-foreign-tuple-preserved')
    db.query('DELETE FROM charsections_dbc WHERE Id=30001;')
    # Missing owned rows are legal on rollback; all remaining 89 must be removed.
    db.query(f'DELETE FROM charsections_dbc WHERE Id={expected[0][0]};')
    state([r for r in installed if r[0] != expected[0][0]], 'one-owned-row-already-deleted')
    db.canonical(ROLLBACK, mode, tag + '-partial-rollback')
    state(baseline, 'partial-rollback-all-90-absent')
    db.canonical(ROLLBACK, mode, tag + '-partial-rollback-repeat')
    state(baseline, 'partial-rollback-repeat')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'work/forest-troll-sql-test-r3')
    args = parser.parse_args()
    output = args.output.resolve()
    require(not output.exists(), 'Output must be fresh: ' + str(output))
    published = json.loads(PUBLISHED.read_text())
    expected = [[r['target_id'], r['race'], r['sex'], r['base'], *r['textures'],
                 r['flags'], r['variation'], r['color']] for r in published['source_to_target']]
    expected.sort()
    require(len(expected) == 90 and [r[0] for r in expected] == list(range(20000, 20090)),
            'Published report must describe exactly IDs 20000..20089')
    require(all(len(r) == 10 and r[7] == 17 for r in expected), 'Published flags/shape drift')
    # This is the only source connection and the only source statement.
    source_env = os.environ.copy()
    source_env.pop('MYSQL_TEST_LOGIN_FILE', None)
    ddl = checked(['mysql', '--login-path=azeroth-dev', '--batch', '--raw',
                   '--skip-column-names', 'acore_world', '-e',
                   'SHOW CREATE TABLE charsections_dbc'], env=source_env).split('\t', 1)[1].rstrip() + ';\n'
    output.mkdir(parents=True)
    (output / 'source-charsections-ddl.sql').write_text(ddl)
    report = dict(status='FAIL', source_access='SHOW CREATE TABLE charsections_dbc only',
                  inputs={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (APPLY, ROLLBACK, PUBLISHED)}, checks=[], runs=[])
    process = None
    try:
        with tempfile.TemporaryDirectory(prefix='ft-mysql-') as short:
            socket = Path(short) / 'm.sock'
            datadir = output / 'mysql'
            datadir.mkdir()
            common = ['/usr/sbin/mysqld', '--no-defaults', '--datadir=' + str(datadir),
                      '--user=' + pwd.getpwuid(os.getuid()).pw_name,
                      '--innodb-buffer-pool-size=32M', '--innodb-redo-log-capacity=8M']
            checked([*common, '--initialize-insecure'])
            process = subprocess.Popen([*common, '--skip-networking', '--mysqlx=OFF',
                                        '--socket=' + str(socket),
                                        '--pid-file=' + str(output / 'mysql.pid'),
                                        '--log-error=' + str(output / 'mysql.log')],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            db = Fixture(socket, output)
            report['runs'] = db.runs
            try:
                for _ in range(120):
                    probe = execute(db.command[:-1], input='SELECT 1;', env=db.env)
                    if probe.returncode == 0:
                        break
                    require(process.poll() is None, 'Private MySQL stopped; inspect mysql.log')
                    time.sleep(.5)
                else:
                    raise RuntimeError('Private MySQL startup timed out')
                checked(db.command[:-1], input='CREATE DATABASE acore_world CHARACTER SET utf8mb4;', env=db.env)
                db.query(ddl)
                report['mysql_version'] = db.query('SELECT VERSION();').strip()
                isolation = db.query('SELECT @@skip_networking, @@datadir, @@socket;').strip().split('\t')
                require(isolation[0] == '1' and Path(isolation[1]).resolve() == datadir
                        and isolation[2] == str(socket), 'Private server isolation mismatch')
                require(db.query("SHOW VARIABLES LIKE 'mysqlx_port';").strip() == '', 'mysqlx enabled')
                report['isolation'] = dict(skip_networking=True, mysqlx=False, datadir=str(datadir))
                columns = [line.split('\t')[0] for line in db.query('SHOW COLUMNS FROM charsections_dbc;').splitlines()]
                require(columns == list(COLUMNS), 'Source column layout changed')
                db.query(insert([SENTINEL]))
                engine = db.engine()
                report['source_engine'] = engine
                require(engine in ('MyISAM', 'InnoDB'), 'Source DDL must use MyISAM or InnoDB')
                report['fixture_starting_engine'] = 'MyISAM'
                default_mode = db.query('SELECT @@SESSION.sql_mode;').strip()
                require('NO_BACKSLASH_ESCAPES' not in default_mode.split(','),
                        'Private default SQL mode unexpectedly disables backslash escapes')
                modes = [default_mode, ','.join(filter(None, [default_mode, 'NO_BACKSLASH_ESCAPES']))]
                report['sql_modes'] = modes
                report['material_findings'] = [
                    'Canonical APPLY converts the copied MyISAM table to InnoDB before its row transaction.',
                    'DDL conversion is not atomic with row changes: migration persists after a later collision refusal; all original rows are preserved. This is accepted behavior.',
                    'Canonical ROLLBACK requires InnoDB and leaves the migrated engine InnoDB; fresh MyISAM rollback refuses without changing rows or engine.'
                ]
                report['test_engine'] = 'InnoDB'
                for mode in modes:
                    tag = 'no-backslash' if 'NO_BACKSLASH_ESCAPES' in mode.split(',') else 'default'
                    db.reset(ddl)
                    # The live schema consists of MEMORY-compatible INT/VARCHAR
                    # columns. Test the real schema, not a substitute table.
                    db.query('ALTER TABLE charsections_dbc ENGINE=MEMORY;')
                    require(db.engine() == 'MEMORY' and db.snapshot() == [SENTINEL],
                            'MEMORY fixture did not preserve source schema rows')
                    db.canonical(APPLY, mode, tag + '-memory-apply',
                                 'target must be InnoDB or MyISAM')
                    require(db.engine() == 'MEMORY' and db.snapshot() == [SENTINEL],
                            'Unsupported-engine refusal altered MEMORY baseline')
                    report['checks'].append(f'{tag}/memory-apply-refused-rows-and-engine-unchanged')
                    db.reset(ddl)
                    suite(db, expected, mode, report['checks'])
                require(db.snapshot() == [SENTINEL], 'Final sentinel state differs')
                require(db.query("SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA='acore_world';").strip() == '0', 'Procedures leaked')
                report['expected_rows'] = expected
                report['final_rows'] = db.snapshot()
                report['final_engine'] = db.engine()
                report['status'] = 'PASS'
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                report['private_mysql_stopped'] = True
    except Exception as exc:
        report['error'] = str(exc)
        raise
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(status=report['status'], report=str(output / 'report.json'),
                              mysql_version=report.get('mysql_version'),
                              checks=len(report['checks']), canonical_runs=len(report['runs']),
                              material_findings=report.get('material_findings', [])), indent=2))


if __name__ == '__main__':
    main()
