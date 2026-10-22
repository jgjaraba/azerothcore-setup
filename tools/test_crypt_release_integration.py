#!/usr/bin/env python3
"""Opt-in real-MySQL release test; never writes to the source DEV database.

Starts a private mysqld with networking disabled. Copies current source table
definitions and one unrelated row per owned table, not the whole world DB.
Uses real stock-client DBCs, representative native server binary samples, and
read-only hardlinks to stock client archives. This is an installer integration
fixture, NOT a booted, complete pristine AzerothCore realm or a gameplay test.
Requires Python 3.11+, mysql, mysqld, mysqldump, and local proprietary inputs.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from unittest.mock import patch

import crypt_release as release
import apply_project_server_data as project_data
from crypt_release_client import file_sha, require
from crypt_release_server_data import DELTAS
from crypt_release_server_db import Database, OWNED, SQL_HASHES, compile_sql


GUARDS = ['dungeon_access_requirements', 'areatrigger_scripts', 'areatrigger_tavern',
          'areatrigger_involvedrelation', 'map_dbc', 'areatable_dbc',
          'mapdifficulty_dbc', 'worldmaparea_dbc']


def run(command, **kwargs):
    result = subprocess.run(list(map(str, command)), text=True, capture_output=True, **kwargs)
    require(result.returncode == 0, f'Command failed: {command[0]}: {result.stderr}')
    return result.stdout


def tree(root):
    return {p.relative_to(root).as_posix(): file_sha(p)
            for p in Path(root).rglob('*') if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--baseline', required=True, type=Path,
                        help='crypt_release_client extract-baseline output')
    parser.add_argument('--archive-root', required=True, type=Path)
    parser.add_argument('--server-data', type=Path, default=Path('/home/dev/azerothcore/env/dist/bin'))
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--source-login-path', default='azeroth-dev')
    parser.add_argument('--mysqld', default='/usr/sbin/mysqld')
    parser.add_argument('--project-workflow', action='store_true',
                        help='Also test apply-db-world.sh with repository assets and the two Turtle SQL files')
    args = parser.parse_args()
    output = args.output.resolve()
    release.disjoint(output, args.bundle, args.baseline, args.archive_root, args.server_data)
    require(not output.exists(), 'Output must be fresh')
    release.verify(args.bundle)
    output.mkdir(parents=True)
    # Do not let a user's login file redirect private-root connections to DEV.
    os.environ['MYSQL_TEST_LOGIN_FILE'] = str(output / 'nonexistent-login-file')
    # Short socket paths avoid the Unix-domain socket path-length limit.
    with tempfile.TemporaryDirectory(prefix='crypt-mysql-') as socket_dir:
        socket = Path(socket_dir) / 'mysql.sock'
        mysql_data = output / 'mysql'
        mysql_data.mkdir()
        common = [args.mysqld, '--no-defaults', '--datadir=' + str(mysql_data),
                  '--innodb-buffer-pool-size=32M', '--innodb-redo-log-capacity=8M']
        run([*common, '--initialize-insecure'])
        process = subprocess.Popen([*map(str, common), '--skip-networking', '--mysqlx=OFF',
                                    '--socket=' + str(socket), '--pid-file=' + str(output / 'mysql.pid'),
                                    '--log-error=' + str(output / 'mysql.log')],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        private = ['mysql', '--no-defaults', '--user=root', '--protocol=SOCKET',
                   '--socket=' + str(socket), '--batch', '--raw', '--skip-column-names']
        try:
            for _ in range(120):
                probe = subprocess.run([*private, '-e', 'SELECT 1'], capture_output=True)
                if probe.returncode == 0:
                    break
                require(process.poll() is None, 'Private mysqld stopped; inspect output/mysql.log')
                time.sleep(.5)
            else:
                raise ValueError('Private mysqld startup timed out')
            database = 'acore_world' if args.project_workflow else 'acore_crypt_release_test'
            run([*private, '-e', f'CREATE DATABASE `{database}` CHARACTER SET utf8mb4;'])
            source = ['mysql', '--login-path=' + args.source_login_path, '--batch', '--raw',
                      '--skip-column-names', '--database=acore_world']
            # The alternate login-file environment applies only to the private
            # server: source queries use the caller's existing read connection.
            source_env = os.environ.copy()
            source_env.pop('MYSQL_TEST_LOGIN_FILE', None)
            ddl = []
            for table in [*OWNED, *GUARDS]:
                result = run([*source, '-e', f'SHOW CREATE TABLE `{table}`;'], env=source_env)
                ddl.append(result.split('\t', 1)[1].rstrip() + ';\n')
            run([*private, database], input=''.join(ddl))
            for table, (pk, ids) in OWNED.items():
                native = run(['mysqldump', '--login-path=' + args.source_login_path,
                              '--no-create-info', '--skip-comments', '--compact', '--skip-add-locks',
                              '--skip-disable-keys', '--set-gtid-purged=OFF', '--no-tablespaces',
                              '--where=' + f'`{pk}` NOT IN ({ids}) ORDER BY `{pk}` LIMIT 1',
                              'acore_world', table], env=source_env)
                run([*private, database], input=native)
            options = output / 'mysql.cnf'
            options.write_text('[client]\nuser=root\nprotocol=SOCKET\nsocket=' + str(socket) + '\n')
            options.chmod(0o600)
            db = Database(database, '', options)
            compiled = compile_sql({n: (args.bundle / 'sql' / n).read_bytes() for n in SQL_HASHES})
            columns = db.schema(compiled)
            require(not db.snapshot(columns), 'Fixture unexpectedly contains pilot SQL')
            db.bindings()
            data, client = output / 'data', output / 'client'
            (data / 'dbc').mkdir(parents=True)
            for name in DELTAS:
                shutil.copyfile(args.baseline / 'dbfilesclient' / name.lower(), data / 'dbc' / name)
            for directory, pattern in [('maps', '000*.map'), ('vmaps', '000*.vmtree'),
                                       ('mmaps', '000*.mmtile'), ('mmaps', '000.mmap')]:
                (data / directory).mkdir(exist_ok=True)
                sample = sorted((args.server_data / directory).glob(pattern))[0]
                shutil.copyfile(sample, data / directory / sample.name)
            # Exercise reuse and rollback of all native shared dependencies.
            for path in (args.bundle / 'server/vmaps').iterdir():
                if not path.name.startswith('800') and path.name != 'Tw800Crypt.wmo.vmo':
                    shutil.copyfile(path, data / 'vmaps' / path.name)
            report = json.loads((args.bundle / 'client/report.json').read_text())
            for archive in report['target_preflight']['archives']:
                target = client / 'Data' / archive['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                os.link(args.archive_root / 'Data' / archive['path'], target)
            before_data, before_client = tree(data), tree(client)
            full_sql = '\n'.join(f'SELECT * FROM `{t}` ORDER BY `{pk}`;'
                                 for t, (pk, _) in OWNED.items())
            before_sql = db.query(full_sql)
            common_args = dict(bundle=args.bundle, data_dir=data, database=database,
                               login_path='', defaults_file=options, client=client, offline=True)
            checks = []

            def restored():
                require(tree(data) == before_data, 'Server data not restored byte-for-byte')
                require(tree(client) == before_client, 'Client files not restored')
                require(db.query(full_sql) == before_sql, 'Unrelated or restored SQL differs')

            state = output / 'state-normal'
            require(release.install(**common_args, state=state)['status'] == 'installed', 'Install failed')
            installed_data = tree(data)
            installed_sql = db.snapshot(columns)
            require(len(installed_sql) == 10, 'Expected exactly ten installed rows')
            require(release.install(**common_args, state=state)['status'] == 'already-installed',
                    'Reapply not idempotent')
            require(tree(data) == installed_data and db.snapshot(columns) == installed_sql,
                    'Reapply changed installed bytes or rows')
            checks.extend(['real MySQL install: ten rows', 'byte-exact idempotent reapply'])
            release.rollback(**common_args, state=state)
            require(release.rollback(**common_args, state=state)['status'] == 'already-rolled-back',
                    'Rollback reapply failed')
            restored()
            checks.append('rollback preserves all original files and unrelated SQL rows')

            atomic = release.atomic
            def disk_failure(path, raw, *rest):
                if Path(path) == data / 'dbc/Map.dbc':
                    raise OSError('injected target-write failure')
                return atomic(path, raw, *rest)
            state = output / 'state-partial'
            with patch.object(release, 'atomic', side_effect=disk_failure):
                try:
                    release.install(**common_args, state=state)
                except OSError:
                    pass
                else:
                    raise ValueError('Injected write failure did not fire')
            require(len(db.snapshot(columns)) == 10, 'Expected committed SQL before target write failure')
            release.rollback(**common_args, state=state, recovery=True)
            restored()
            checks.append('recover after real SQL commit and partial file installation')

            save = release.save
            def precommit_failure(state_path, journal):
                save(state_path, journal)
                if journal['phase'] == 'db_intent' and journal['db_after']:
                    raise OSError('injected failure before COMMIT')
            state = output / 'state-precommit'
            with patch.object(release, 'save', side_effect=precommit_failure):
                try:
                    release.install(**common_args, state=state)
                except OSError:
                    pass
                else:
                    raise ValueError('Injected precommit failure did not fire')
            require(not db.snapshot(columns), 'Uncommitted transaction was not rolled back')
            release.rollback(**common_args, state=state, recovery=True)
            restored()
            checks.append('real MySQL rollback on connection close before COMMIT')

            transaction = Database.transaction
            def lost_ack(instance, statements, cols, before, persist):
                transaction(instance, statements, cols, before, persist)
                raise OSError('injected loss after COMMIT acknowledgement')
            state = output / 'state-lost-ack'
            with patch.object(Database, 'transaction', new=lost_ack):
                try:
                    release.install(**common_args, state=state)
                except OSError:
                    pass
                else:
                    raise ValueError('Injected acknowledgement failure did not fire')
            require(len(db.snapshot(columns)) == 10, 'Commit did not reach private MySQL')
            release.rollback(**common_args, state=state, recovery=True)
            restored()
            checks.append('recover committed SQL with install still at db_intent')

            # Exercise the portable copy, not just imports from the checkout.
            state = output / 'state-standalone'
            cli = ['python3', args.bundle / 'crypt_release.py', 'install', '--bundle', args.bundle,
                   '--data-dir', data, '--state', state, '--database', database,
                   '--login-path', '', '--defaults-file', options, '--client', client, '--offline']
            result = json.loads(run(cli))
            require(result['status'] == 'installed', 'Standalone CLI install failed')
            cli[2] = 'rollback'
            require(json.loads(run(cli))['status'] == 'rolled-back', 'Standalone CLI rollback failed')
            restored()
            checks.append('standalone bundled CLI install and rollback')
            if args.project_workflow:
                # The canonical SQL contains USE acore_world. This name belongs
                # only to our private no-network MySQL instance, not the DEV DB.
                run(['mysql_config_editor', 'set', '--login-path=crypt-project-test',
                     '--user=root', '--socket=' + str(socket)])
                sql_dir = output / 'project-sql'
                sql_dir.mkdir()
                for name in SQL_HASHES:
                    shutil.copyfile(args.bundle / 'sql' / name, sql_dir / name)
                (sql_dir / 'manifest.txt').write_text(''.join(n + '\n' for n in SQL_HASHES))
                env = os.environ.copy()
                env.pop('MANIFEST', None)
                env.update(SQL_DIR=str(sql_dir), LOGIN_PATH='crypt-project-test')
                state = output / 'state-project-workflow'
                manifest = release.ROOT / 'data/server/manifest.json'
                command = [release.ROOT / 'scripts/apply-db-world.sh', '--with-server-data',
                           '--data-dir', data, '--state-dir', state, '--offline']
                run(command, env=env)
                installed = tree(data)
                rows = db.snapshot(columns)
                require(len(rows) == 10, 'Project script did not install ten pilot SQL rows')
                run(command, env=env)
                require(tree(data) == installed and db.snapshot(columns) == rows,
                        'Project script reapply changed bytes or SQL rows')
                require(tree(client) == before_client, 'Project script unexpectedly modified client')
                project_data.rollback(manifest, data, state, offline=True)
                require(db.snapshot(columns) == rows, 'File-only rollback unexpectedly changed SQL')
                db.transaction(release.deletes(), columns, rows,
                               lambda value: require(not value, 'Fixture cleanup failed'))
                restored()
                checks.append('existing apply-db-world.sh: real canonical SQL + 430 repository files, idempotent')
                checks.append('project file-only rollback leaves SQL intact and never touches clients')
                collision = data / 'maps/8005234.map'
                collision.write_bytes(b'injected collision')
                command[command.index('--state-dir') + 1] = output / 'state-preflight-refused'
                rejected = subprocess.run(list(map(str, command)), env=env,
                                          text=True, capture_output=True)
                require(rejected.returncode != 0 and not db.snapshot(columns),
                        'Project preflight failed to stop before SQL')
                require(not (output / 'state-preflight-refused').exists(), 'Refused preflight created state')
                collision.unlink()
                restored()
                checks.append('project binary collision stops before any SQL or state mutation')
            result = dict(status='PASS', checks=checks, bundle=release.verify(args.bundle),
                          sql_engine='private MySQL; networking disabled',
                          baseline='stock DBCs + representative native server files + schema/unrelated-row fixture',
                          not_tested=['full pristine realm startup', 'client launch/gameplay',
                                      'all-project restore', 'from-source rebuild'])
            (output / 'report.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
            print(json.dumps(result, indent=2, sort_keys=True))
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=60)


if __name__ == '__main__':
    main()
