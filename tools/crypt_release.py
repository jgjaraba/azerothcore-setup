#!/usr/bin/env python3
"""Portable clean-server crypt release.

Build creates a deterministic, inventoried folder (copy the entire folder).
Install/rollback require --offline: the operator asserts server and client are
stopped and no other writer will modify their files or world database. Python
3.11+ and the mysql CLI are the only installation dependencies.

An interrupted operation is never automatically resumed. Use `recover` with
the same arguments to restore originals, then use a fresh --state for another
install. Recovery accepts only original or recorded installed bytes/SQL rows;
external edits require manual reconciliation before retry. Preserve STATE and
BUNDLE together until rollback is no longer needed. State is local trusted
operator data, not an importable third-party manifest.

If preparation fails before journal.json is first saved, no target files or SQL
have been changed. Install and recover diagnose this incomplete preparation;
remove only that incomplete STATE directory or choose a fresh --state. This
applies to trusted preparation state, never to an installed state whose journal
has been deleted: preserve installed journals and backups for recovery.
"""
import sys
sys.dont_write_bytecode = True

import argparse
import contextlib
import fcntl
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile

from crypt_release_client import require, sha, file_sha, relative, stock_path
from crypt_release_server_data import server_payload, merge_server, baseline_check, DELTAS
from crypt_release_server_db import Database, compile_sql, deletes, SQL_HASHES

ROOT = Path(__file__).resolve().parent.parent
CODE = ['crypt_release.py', 'crypt_release_client.py', 'crypt_release_dbc.py',
        'crypt_release_server_data.py', 'crypt_release_server_db.py']


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def durable_mkdir(path):
    missing = []
    for parent in (Path(path), *Path(path).parents):
        require(not parent.is_symlink(), f'Symlink directory: {parent}')
        if parent.exists():
            require(parent.is_dir(), f'Not a directory: {parent}')
            break
        missing.append(parent)
    for directory in reversed(missing):
        directory.mkdir()
        fsync_dir(directory.parent)


def atomic(path, raw, mode=0o600):
    """Caller journals intent before invoking this function on target files."""
    path = Path(path)
    fd, tmp = tempfile.mkstemp(prefix='.crypt-release-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            os.fchmod(stream.fileno(), mode)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        fsync_dir(path.parent)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def safe_path(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        require(not part.is_symlink(), f'Symlink path: {part}')
    require(not path.exists() or path.is_file(), f'Not a regular file: {path}')
    return path


def digest_or_none(path):
    path = safe_path(path)
    return file_sha(path) if path.exists() else None


def disjoint(*paths):
    paths = [Path(p).resolve() for p in paths if p is not None]
    for i, first in enumerate(paths):
        for second in paths[i + 1:]:
            require(not first.is_relative_to(second) and not second.is_relative_to(first),
                    f'Overlapping paths: {first}, {second}')


def build(server_data, client_release, output):
    server_data, client_release, output = map(lambda p: Path(p).resolve(),
                                            (server_data, client_release, output))
    disjoint(output, server_data, client_release)
    require(not output.exists(), 'Output must be fresh')
    payload = {'server/' + name: raw for name, raw in server_payload(server_data).items()}
    report_raw = (client_release / 'report.json').read_bytes()
    report = json.loads(report_raw)
    require(report['kind'] == 'crypt-clean-client' and report['artifact']['path'] == 'Data/patch-T.MPQ',
            'Expected clean-client release report')
    archive = (client_release / 'Data/patch-T.MPQ').read_bytes()
    require(sha(archive) == report['artifact']['sha256'] and len(archive) == report['artifact']['size'],
            'Client artifact/report mismatch')
    payload['client/Data/patch-T.MPQ'] = archive
    payload['client/report.json'] = report_raw
    for name in CODE:
        payload[name] = (Path(__file__).parent / name).read_bytes()
    sql = {name: (ROOT / 'data/sql/custom/db_world' / name).read_bytes() for name in SQL_HASHES}
    compile_sql(sql)
    payload.update({'sql/' + name: raw for name, raw in sql.items()})
    inventory = {name: dict(size=len(raw), sha256=sha(raw)) for name, raw in sorted(payload.items())}
    manifest = dict(schema=1, kind='crypt-portable-release', files=inventory,
                    model_closure=405, sql_rows=10, server_dbc_tables=5)
    output.mkdir(parents=True)
    for name, raw in sorted(payload.items()):
        path = output / relative(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        os.utime(path, (0, 0))
    (output / 'manifest.json').write_bytes(json_bytes(manifest))
    os.utime(output / 'manifest.json', (0, 0))
    return verify(output)


def verify(bundle):
    bundle = Path(bundle)
    safe_path(bundle / 'manifest.json')
    raw = (bundle / 'manifest.json').read_bytes()
    manifest = json.loads(raw)
    require(manifest['schema'] == 1 and manifest['kind'] == 'crypt-portable-release', 'Unknown bundle format')
    files = manifest['files']
    require(set(CODE + ['client/report.json', 'client/Data/patch-T.MPQ'] +
                ['sql/' + n for n in SQL_HASHES]) <= set(files), 'Incomplete bundle')
    found = set()
    for path in bundle.rglob('*'):
        require(not path.is_symlink(), 'Symlink in bundle')
        if path.is_file():
            found.add(path.relative_to(bundle).as_posix())
    require(found == set(files) | {'manifest.json'}, 'Unexpected/missing bundle files')
    for name, record in files.items():
        path = safe_path(bundle / relative(name))
        require(path.stat().st_size == record['size'] and file_sha(path) == record['sha256'],
                f'Bundle hash mismatch: {name}')
    compile_sql({n: (bundle / 'sql' / n).read_bytes() for n in SQL_HASHES})
    # A release is an integrity envelope, not a signature/authenticity assertion.
    return dict(status='PASS', bundle_sha256=sha(raw), files=len(files))


def archive(bundle, output):
    """Transport archive with fixed order, ownership, modes and timestamps."""
    bundle, output = Path(bundle).resolve(), Path(output).absolute()
    disjoint(bundle, output)
    require(not output.exists(), 'Archive output must be fresh')
    original = verify(bundle)
    manifest = json.loads((bundle / 'manifest.json').read_text())
    with tarfile.open(output, 'x', format=tarfile.PAX_FORMAT) as stream:
        for name in sorted([*manifest['files'], 'manifest.json']):
            raw = (bundle / relative(name)).read_bytes()
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(raw), 0o644, 0
            stream.addfile(info, io.BytesIO(raw))
    require(verify(bundle) == original, 'Bundle changed while archiving')
    return dict(status='PASS', archive_sha256=file_sha(output), size=output.stat().st_size,
                bundle_sha256=original['bundle_sha256'])


def client_check(client, report, owned=None):
    """Exact stock archive set, with only the journal-owned T exception."""
    client = Path(client)
    require((client / 'Data').is_dir(), 'Missing client Data')
    for path in client.iterdir():
        require(path.name.lower() not in ('dbfilesclient', 'world', 'textures', 'interface'),
                'Loose client resource override')
    expected = {r['path']: r for r in report['target_preflight']['archives']}
    require(expected and all(stock_path(n) for n in expected), 'Invalid client baseline')
    found = {}
    for path in (client / 'Data').rglob('*'):
        require(not path.is_symlink(), 'Symlink client Data')
        if not path.is_file():
            continue
        name = path.relative_to(client / 'Data').as_posix()
        if name == 'patch-T.MPQ' and owned is not None:
            require(file_sha(path) == owned, 'Owned client patch changed')
            continue
        if path.suffix.lower() == '.mpq':
            require(stock_path(name), f'Unknown client archive: {name}')
            found[name] = path
        else:
            require(path.suffix.lower() in ('.html', '.url', '.wtf') and
                    not any(p.lower() in ('dbfilesclient', 'world', 'textures', 'interface')
                            for p in path.relative_to(client / 'Data').parts), 'Loose client Data override')
    require(set(found) == set(expected), 'Client archive set differs from baseline')
    for name, path in found.items():
        require(path.stat().st_size == expected[name]['size'] and
                file_sha(path) == expected[name]['sha256'], f'Client baseline hash mismatch: {name}')


def save(state, journal):
    atomic(Path(state) / 'journal.json', json_bytes(journal))


def identity(bundle, data_dir, database, client):
    return dict(bundle_sha256=verify(bundle)['bundle_sha256'], data_dir=str(Path(data_dir).resolve()),
                database=database, client=str(Path(client).resolve()) if client else None)


def target_plan(bundle, data_dir, client):
    bundle, data_dir = Path(bundle), Path(data_dir)
    baseline_check(data_dir)
    for directory in ('maps', 'vmaps', 'mmaps'):
        require(not any((data_dir / directory).glob('800*')),
                f'Fresh target has occupied map800 {directory} paths')
    manifest = json.loads((bundle / 'manifest.json').read_text())
    server = {n.removeprefix('server/'): (bundle / n).read_bytes()
              for n in manifest['files'] if n.startswith('server/')}
    merged = merge_server(data_dir, server)
    result = {str(safe_path(data_dir / name)): raw for name, raw in merged.items()}
    for name, raw in server.items():
        if name.startswith('dbc/'):
            continue
        path = safe_path(data_dir / name)
        if path.exists():
            # Shared models may be reused, but map-specific files need clean IDs.
            require(name.startswith('vmaps/') and not Path(name).name.startswith('800') and
                    path.read_bytes() == raw, f'Server payload collision: {name}')
        result[str(path)] = raw
    if client:
        report = json.loads((bundle / 'client/report.json').read_text())
        client_check(client, report)
        path = safe_path(Path(client) / 'Data/patch-T.MPQ')
        require(not path.exists(), 'Client T already exists without owned state')
        result[str(path)] = (bundle / 'client/Data/patch-T.MPQ').read_bytes()
    return result


@contextlib.contextmanager
def locked(state):
    # The containing state directory is created only after all read-only preflight.
    path = Path(state) / 'lock'
    safe_path(path)
    with path.open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('Another operation owns this state') from exc
        yield


def journal_path(state):
    state = Path(state)
    path = safe_path(state / 'journal.json')
    if state.is_dir():
        require(path.exists(),
                'State preparation interrupted before journal; no target files or SQL were changed; '
                'remove only this incomplete state directory or choose a fresh --state. '
                'This diagnosis assumes the journal was not deleted from an installed state.')
    return path


def read_journal(state, expected):
    journal = json.loads(journal_path(state).read_text())
    require(journal['identity'] == expected, 'State belongs to a different bundle/target/database/client')
    require(journal['schema'] == 1, 'Unknown journal format')
    require(journal['phase'] in ('prepared', 'db_intent', 'db_committed', 'installed',
                                 'rollback_intent', 'rolled_back'), 'Unknown journal phase')
    for item in journal['files']:
        safe_path(item['path'])
        if item['before'] is not None:
            backup = safe_path(Path(state) / relative(item['backup']))
            require(file_sha(backup) == item['before'], 'Original backup changed')
    return journal


def check_files(journal, recovery=False):
    for item in journal['files']:
        actual = digest_or_none(item['path'])
        permitted = {item['after'], item['before']} if recovery else {item['after']}
        require(actual in permitted, f'Owned file changed: {item["path"]}')


def install(bundle, data_dir, state, database, login_path='azeroth-dev', client=None,
            offline=False, defaults_file=None, mysql='mysql'):
    require(offline, '--offline is required (server/client stopped, exclusive operator access)')
    bundle, data_dir, state = map(lambda p: Path(p).absolute(), (bundle, data_dir, state))
    disjoint(bundle, data_dir, state, client)
    if state.exists():
        journal_path(state)
    ident = identity(bundle, data_dir, database, client)
    db = Database(database, login_path, defaults_file, mysql)
    ident['database_server_uuid'] = db.server_identity()
    compiled = compile_sql({n: (bundle / 'sql' / n).read_bytes() for n in SQL_HASHES})
    columns = db.schema(compiled)
    db.bindings()
    if state.exists():
        journal = read_journal(state, ident)
        require(journal['phase'] == 'installed', 'Incomplete/retired state: use recover or a fresh state')
        require(columns == journal['columns'], 'Database schema changed')
        check_files(journal)
        require(db.snapshot(columns) == journal['db_after'], 'Owned SQL rows changed')
        if client:
            report = json.loads((bundle / 'client/report.json').read_text())
            client_check(client, report, report['artifact']['sha256'])
        return dict(status='already-installed')
    plan = target_plan(bundle, data_dir, client)
    before = db.snapshot(columns)
    require(not before, 'Fresh install requires all ten pilot SQL rows absent')
    originals = {path: digest_or_none(path) for path in plan}
    # No target files or SQL have been modified before this point.
    safe_path(state / 'journal.json')
    durable_mkdir(state)
    with locked(state):
        (state / 'backups').mkdir()
        entries, directories = [], set()
        for i, (path, raw) in enumerate(sorted(plan.items())):
            item = dict(path=path, before=originals[path], after=sha(raw), backup=f'backups/{i}',
                        mode=(Path(path).stat().st_mode & 0o777) if originals[path] is not None else 0o644)
            require(digest_or_none(path) == item['before'], 'Target changed during preflight')
            if item['before'] is not None:
                atomic(state / item['backup'], Path(path).read_bytes())
            for parent in Path(path).parents:
                if parent.exists():
                    break
                directories.add(str(parent))
            entries.append(item)
        journal = dict(schema=1, identity=ident, phase='prepared', files=entries,
                       directories=sorted(directories, key=lambda p: (len(Path(p).parts), p)),
                       columns=columns, db_before=before, db_after=None)
        save(state, journal)
        journal['phase'] = 'db_intent'
        save(state, journal)
        def persist(snapshot):
            require(len(snapshot) == 10, 'Unexpected installed SQL row count')
            journal['db_after'] = snapshot
            save(state, journal)
        db.transaction([stmt for _, _, stmt in compiled], columns, before, persist)
        journal['phase'] = 'db_committed'
        save(state, journal)
        # Global durable intent records every original, absence, and generated hash.
        for directory in journal['directories']:
            Path(directory).mkdir(exist_ok=True)
            fsync_dir(Path(directory).parent)
        for item in entries:
            require(digest_or_none(item['path']) == item['before'], 'Target changed after preflight')
            if item['after'] != item['before']:
                atomic(item['path'], plan[item['path']], item['mode'])
        journal['phase'] = 'installed'
        save(state, journal)
    return dict(status='installed', files=len(entries), sql_rows=10, state=str(state))


def rollback(bundle, data_dir, state, database, login_path='azeroth-dev', client=None,
             offline=False, defaults_file=None, mysql='mysql', recovery=False):
    require(offline, '--offline is required (server/client stopped, exclusive operator access)')
    disjoint(bundle, data_dir, state, client)
    state = Path(state).absolute()
    journal_path(state)
    ident = identity(bundle, data_dir, database, client)
    db = Database(database, login_path, defaults_file, mysql)
    ident['database_server_uuid'] = db.server_identity()
    journal = read_journal(state, ident)
    if journal['phase'] == 'rolled_back':
        for item in journal['files']:
            require(digest_or_none(item['path']) == item['before'], 'Restored file changed')
    elif not recovery:
        require(journal['phase'] == 'installed', 'Interrupted operation: use recover')
    compiled = compile_sql({n: (Path(bundle) / 'sql' / n).read_bytes() for n in SQL_HASHES})
    columns = db.schema(compiled)
    require(columns == journal['columns'], 'Database schema changed')
    db.bindings()
    current = db.snapshot(columns)
    partial = journal['phase'] != 'installed'
    check_files(journal, partial)
    require(current == journal['db_after'] or (partial and current == journal['db_before']),
            'Owned SQL rows changed; reconcile manually before recovery')
    if journal['phase'] == 'rolled_back':
        require(current == journal['db_before'], 'Restored SQL changed')
        return dict(status='already-rolled-back')
    # All rollback/recovery checks finish before any mutation.
    with locked(state):
        journal['phase'] = 'rollback_intent'
        save(state, journal)
        if current:
            db.transaction(deletes(), columns, current, lambda rows: require(not rows, 'Rollback SQL remains'))
        for item in journal['files']:
            path = Path(item['path'])
            if digest_or_none(path) == item['before']:
                continue
            require(digest_or_none(path) == item['after'], 'Owned file changed during rollback')
            if item['before'] is None:
                path.unlink()
                fsync_dir(path.parent)
            else:
                atomic(path, (state / item['backup']).read_bytes(), item['mode'])
        for directory in reversed(journal['directories']):
            path = Path(directory)
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
                fsync_dir(path.parent)
        journal['phase'] = 'rolled_back'
        save(state, journal)
    return dict(status='rolled-back')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('build')
    p.add_argument('--server-data', type=Path, default=Path('/home/dev/azerothcore/env/dist/bin'))
    p.add_argument('--client-release', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('verify')
    p.add_argument('--bundle', type=Path, required=True)
    p = sub.add_parser('archive')
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    for command in ('install', 'rollback', 'recover'):
        p = sub.add_parser(command)
        for name in ('bundle', 'data-dir', 'state'):
            p.add_argument('--' + name, type=Path, required=True)
        p.add_argument('--database', required=True)
        p.add_argument('--login-path', default='azeroth-dev')
        p.add_argument('--defaults-file', type=Path, help='mysql extra option file (first CLI option)')
        p.add_argument('--mysql', default='mysql', help='mysql client executable')
        p.add_argument('--client', type=Path)
        p.add_argument('--offline', action='store_true')
    args = vars(parser.parse_args())
    command = args.pop('command')
    try:
        if command == 'recover':
            result = rollback(**args, recovery=True)
        else:
            result = globals()[command](**args)
        print(json.dumps(result, indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        parser.exit(1, f'ERROR: {exc}\n')


if __name__ == '__main__':
    main()
