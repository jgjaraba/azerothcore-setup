#!/usr/bin/env python3
"""Apply repository server data, independently of SQL and manual client setup.

Schema 1: {"schema": 1, "files": {"turtle-crypt/dbc/Map.dbc":
{"path": "dbc/Map.dbc", "sha256": "<64 lowercase hex>", "size": 123,
 "kind": "dbc-delta"}, ...}}. Keys must be sorted source-relative POSIX
paths. All regular files below the manifest's directory, except the manifest,
must be inventoried. Copy entries target maps/, vmaps/ or mmaps/. DBC deltas
use the five existing DELTAS definitions, plus an optional facial-style-delta
for CharacterFacialHairStyles.dbc keyed by (Race, Sex, Variation), without an ID.

Schema 2 adds a required geography object with vmap_tiles (complete sorted map0
tile paths), model_closure (complete sorted referenced model paths), mmap_tiles
(complete sorted regional/halo MMap paths), and map_dependencies (terrain path
-> accepted SHA256 list). It supports kind
replace with accepted_before (known native SHA256 list), and additive-dbc for
AreaTable/WMOAreaTable/WorldMapArea/WorldMapOverlay. DBC donors may share a
target and are merged in sorted source-path order, preserving destination rows
and strings. All binary kinds accept absence or identical content; replace
additionally accepts only the explicitly recorded native hashes. No force mode.

check emits a read-only plan suitable for install --expected-plan. --offline
asserts the server is stopped and exclusive access continues from check through
SQL and install. SQL is not journaled or rolled back here. Preserve the manifest,
source files and state for rollback/recover. Interrupted preparation without a
journal changed no target files; choose fresh state or remove only that incomplete
state (assuming no installed journal was manually deleted).
"""
import sys
sys.dont_write_bytecode = True

import argparse
import json
import os
import re
import struct
from pathlib import Path

from crypt_release import (atomic, safe_path, durable_mkdir, disjoint, locked,
                           fsync_dir, digest_or_none, json_bytes)
from crypt_release_client import require, sha, file_sha, relative
from crypt_release_dbc import parse_dbc, merge_dbc
from crypt_release_server_data import DELTAS, binary_check, baseline_check, merge_server, tile_models


# Schema 2 adds guarded binary replacements, ordered additive donors and a
# coordinated map contract. Schema 1 retains its exact pilot requirements.
ADDITIVE_DBC = {
    'dbc/AreaTable.dbc': (36, list(range(11, 27))),
    'dbc/WMOAreaTable.dbc': (28, list(range(11, 27))),
    'dbc/WorldMapArea.dbc': (11, [3]),
    'dbc/WorldMapOverlay.dbc': (17, [8]),
}


class Payload(dict):
    def __init__(self):
        super().__init__()
        self.donors = []
        self.replacements = {}
        self.contract = None


def hashes(values):
    require(isinstance(values, list) and values and len(set(values)) == len(values) and
            all(isinstance(h, str) and re.fullmatch('[0-9a-f]{64}', h) for h in values),
            'Invalid accepted hashes')


def geography_check(payload, root=None):
    """Validate the atomic full-tree unit and its effective navigation inputs."""
    c = payload.contract
    if c is None:
        return {}
    require(set(c) == {'vmap_tiles', 'model_closure', 'mmap_tiles', 'map_dependencies'},
            'Unknown geography contract fields')
    tiles = sorted(n for n in payload if re.fullmatch(r'vmaps/000_\d\d_\d\d.vmtile', n))
    require('vmaps/000.vmtree' in payload and tiles == c['vmap_tiles'],
            'Incomplete VMap fullset')
    models = sorted({'vmaps/' + model for n in tiles for model in tile_models(payload[n])})
    require(models == c['model_closure'] and all(n in payload for n in models),
            'Incomplete VMap model closure')
    for n, accepted in c['map_dependencies'].items():
        require(re.fullmatch(r'maps/000\d{4}.map', n), 'Invalid halo dependency path')
        hashes(accepted)
        if n in payload:
            require(sha(payload[n]) in accepted, f'Halo dependency mismatch: {n}')
    require('mmaps/000.mmap' in payload, 'Missing coordinated MMap params')
    require(sorted(n for n in payload if re.fullmatch(r'mmaps/000\d{4}.mmtile', n)) ==
            c['mmap_tiles'], 'Incomplete regional/halo MMap fullset')
    if root is None:
        return {}
    dependencies = {}
    existing = {p.relative_to(root).as_posix() for p in (root / 'vmaps').glob('000*.vmtile')}
    require(existing <= set(tiles), 'Stale installed VMap tiles outside fullset')
    for n, accepted in c['map_dependencies'].items():
        path = safe_path(root / n)
        actual = sha(payload[n]) if n in payload else file_sha(path)
        require(actual in accepted, f'Halo dependency mismatch: {n}')
        if n not in payload:
            dependencies[n] = actual
    params = struct.unpack('<5f2I', payload['mmaps/000.mmap'])
    native_path = safe_path(root / 'mmaps/000.mmap')
    native = struct.unpack('<5f2I', native_path.read_bytes())
    require(params[:5] == native[:5] and params[6] == native[6] and
            params[5] > 0 and params[6] > 0, 'MMap params compatibility mismatch')
    survivors = {}
    for p in (root / 'mmaps').glob('000*.mmtile'):
        safe_path(p)
        n = p.relative_to(root).as_posix()
        if n not in payload:
            survivors[n] = p.read_bytes()
            dependencies[n] = sha(survivors[n])
    survivors.update({n: raw for n, raw in payload.items()
                      if re.fullmatch(r'mmaps/000\d{4}.mmtile', n)})
    coordinates = set()
    for n, raw in survivors.items():
        binary_check(n, raw)
        require(len(raw) >= 156, f'Truncated Detour mesh header: {n}')
        header = struct.unpack_from('<15I', raw, 56)
        coord = tuple(header[2:5])
        require(coord not in coordinates and 0 < header[6] <= params[6],
                f'MMap duplicate coordinate/poly capacity: {n}')
        coordinates.add(coord)
    require(len(survivors) <= params[5], 'Insufficient MMap tile capacity')
    return dependencies


FACIAL_STYLE_TARGET = 'dbc/CharacterFacialHairStyles.dbc'
FACIAL_STYLE_ROWS = {
    (8, 0, 11): (0, 2, 0, 0, 0),
    (8, 0, 12): (0, 4, 0, 0, 0),
    (8, 0, 13): (0, 6, 0, 0, 0),
    (8, 1, 6): (0, 2, 0, 0, 0),
    (8, 1, 7): (0, 3, 0, 0, 0),
    (8, 1, 8): (0, 4, 0, 0, 0),
    (8, 1, 9): (0, 5, 0, 0, 0),
}
TAUREN_FACIAL_STYLE_ROWS = {
    (6, 0, 7): (10, 10, 10, 0, 0),
    (6, 0, 8): (11, 11, 11, 0, 0),
    (6, 1, 5): (0, 0, 6, 0, 0),
    (6, 1, 6): (0, 0, 7, 0, 0),
}


def parse_natural_dbc(raw):
    """Eight unsigned columns, no row ID; retain the original string block."""
    require(len(raw) >= 20, 'Truncated natural-key DBC header')
    magic, count, fields, width, size = struct.unpack_from('<4s4I', raw)
    require(magic == b'WDBC' and fields == 8 and width == 32,
            'Invalid natural-key DBC schema (expected WDBC, 8 fields, 32 bytes)')
    end = 20 + count * width
    require(len(raw) == end + size, 'Invalid natural-key DBC length')
    block = raw[end:]
    require(block and block[0] == 0 and block[-1] == 0,
            'Invalid natural-key DBC string block')
    rows = list(struct.iter_unpack('<8I', raw[20:end]))
    keys = [row[:3] for row in rows]
    require(len(set(keys)) == len(keys), 'Duplicate natural-key DBC key')
    return rows, block


def merge_natural_dbc(native, donor):
    """Keep native records byte-for-byte and append missing rows in key order."""
    rows, block = parse_natural_dbc(native)
    additions, _ = parse_natural_dbc(donor)
    existing = {row[:3]: row for row in rows}
    for row in additions:
        require(row[:3] not in existing or existing[row[:3]] == row,
                f'Natural-key DBC collision: {row[:3]}')
    missing = sorted(row for row in additions if row[:3] not in existing)
    return (struct.pack('<4s4I', b'WDBC', len(rows) + len(missing), 8, 32, len(block)) +
            native[20:20 + len(rows) * 32] +
            b''.join(struct.pack('<8I', *row) for row in missing) + block)


def canonical(name):
    require(isinstance(name, str), 'Path must be a string')
    path = relative(name)
    require(path.as_posix() == name, f'Non-canonical path: {name}')
    return path


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def load_json(raw):
    return json.loads(raw, object_pairs_hook=unique_object)


def inventory(manifest):
    manifest = safe_path(manifest)
    raw = manifest.read_bytes()
    document = load_json(raw)
    require(document['schema'] in (1, 2) and set(document) ==
            ({'schema', 'files'} if document['schema'] == 1 else {'schema', 'files', 'geography'}),
            'Unknown server data manifest schema')
    files = document['files']
    require(isinstance(files, dict) and files and list(files) == sorted(files),
            'Manifest files must be nonempty and sorted')
    found = set()
    for path in manifest.parent.rglob('*'):
        require(not path.is_symlink(), f'Symlink source: {path}')
        require(path.is_dir() or path.is_file(), f'Non-regular source: {path}')
        if path.is_file() and path != manifest:
            found.add(path.relative_to(manifest.parent).as_posix())
    require(found == set(files), 'Manifest coverage mismatch (missing/unlisted files)')
    payload, kinds = Payload(), {}
    payload.contract = document.get('geography')
    require(document['schema'] == 1 or isinstance(payload.contract, dict),
            'Schema 2 requires a geography contract')
    for name, record in files.items():
        source = safe_path(manifest.parent / canonical(name))
        extra = {'accepted_before'} if record['kind'] == 'replace' else set()
        require(set(record) == {'path', 'sha256', 'size', 'kind'} | extra, 'Unknown entry fields')
        require(document['schema'] == 2 or record['kind'] not in ('replace', 'additive-dbc'),
                'Entry requires schema 2')
        target = canonical(record['path']).as_posix()
        require(target not in payload or (document['schema'] == 2 and
                record['kind'] in ('dbc-delta', 'additive-dbc') and
                kinds[target] in ('dbc-delta', 'additive-dbc')), f'Duplicate target: {target}')
        require(type(record['size']) is int and record['size'] >= 0 and
                isinstance(record['sha256'], str) and
                re.fullmatch('[0-9a-f]{64}', record['sha256']), 'Invalid size/hash')
        data = source.read_bytes()
        require(len(data) == record['size'] and sha(data) == record['sha256'],
                f'Source hash/size mismatch: {name}')
        kind = record['kind']
        if kind == 'dbc-delta':
            require(target in {'dbc/' + n for n in DELTAS}, 'Unknown pilot DBC delta')
            fields, ids, strings, order = DELTAS[Path(target).name]
            n, rows, _ = parse_dbc(data)
            require(n == fields and {r[0] for r in rows} == set(ids),
                    f'Expected compact pilot donor: {target}')
            # Validate all declared string offsets through the existing merger.
            merge_dbc(data, data, ids, strings, order)
            if target == 'dbc/Map.dbc':
                require(rows[0][57] == 0, 'Server Map loading screen must remain zero')
        elif kind == 'additive-dbc':
            require(target in ADDITIVE_DBC, 'Unknown additive DBC target')
            fields, strings = ADDITIVE_DBC[target]
            n, rows, _ = parse_dbc(data)
            require(n == fields and rows, f'Invalid additive DBC schema: {target}')
            merge_dbc(data, data, [r[0] for r in rows], strings)
        elif kind == 'facial-style-delta':
            require(target == FACIAL_STYLE_TARGET, 'Unknown facial-style DBC target')
            rows, _ = parse_natural_dbc(data)
            mapped = {row[:3]: row[3:] for row in rows}
            require(mapped in (FACIAL_STYLE_ROWS, {**FACIAL_STYLE_ROWS, **TAUREN_FACIAL_STYLE_ROWS}),
                    'Expected seven Troll rows or complete Tauren facial-style extension')
        else:
            require(kind in ('copy', 'replace'), f'Unknown entry kind: {kind}')
            if kind == 'replace':
                hashes(record['accepted_before'])
                payload.replacements[target] = record['accepted_before']
            path = Path(target)
            suffixes = {'maps': {'.map'}, 'vmaps': {'.vmtree', '.vmtile', '.vmo', '.m2'},
                        'mmaps': {'.mmap', '.mmtile'}}
            require(len(path.parts) == 2 and path.parts[0] in suffixes and
                    path.suffix in suffixes[path.parts[0]], f'Unsupported copy target: {target}')
            binary_check(target, data)
            if path.parts[0] == 'vmaps' and path.suffix in {'.vmo', '.m2'}:
                require(data[:8] == b'VMAP_4.8', f'Incompatible collision model header: {target}')
        if kind in ('dbc-delta', 'additive-dbc'):
            payload.donors.append((target, kind, data))
        payload[target], kinds[target] = data, kind
    require({n for n, k, _ in payload.donors if k == 'dbc-delta'} ==
             {'dbc/' + n for n in DELTAS}, 'All five pilot DBC deltas are required')
    # Detect conflicting durable donors during source-only validation too,
    # without waiting for target access or letting a later donor mask a row.
    combined = {}
    for target, kind, data in payload.donors:
        if kind == 'dbc-delta':
            fields, ids, strings, order = DELTAS[Path(target).name]
        else:
            fields, strings = ADDITIVE_DBC[target]
            ids, order = [r[0] for r in parse_dbc(data)[1]], False
        empty = struct.pack('<4s4I', b'WDBC', 0, fields, fields * 4, 1) + b'\0'
        combined[target] = merge_dbc(combined.get(target, empty), data, ids, strings, order)
    geography_check(payload)
    return sha(raw), payload


def identity(manifest, data_dir, manifest_sha):
    return dict(manifest=str(Path(manifest).absolute()), manifest_sha256=manifest_sha,
                data_dir=str(Path(data_dir).absolute()))


def read_state(state, ident):
    path = safe_path(Path(state) / 'journal.json')
    require(path.is_file(), 'State preparation interrupted before journal; no target files changed. '
            'Use fresh state or remove only incomplete state; preserve installed journals.')
    journal = load_json(path.read_bytes())
    require(journal['schema'] == 1 and journal['identity'] == ident, 'State identity mismatch')
    require(journal['phase'] in ('prepared', 'installed', 'rollback_intent', 'rolled_back'),
            'Unknown state phase')
    for item in journal['files']:
        require(Path(item['path']).is_relative_to(Path(ident['data_dir'])), 'Invalid journal target')
        safe_path(item['path'])
        if item['before'] is not None:
            backup = safe_path(Path(state) / canonical(item['backup']))
            require(file_sha(backup) == item['before'], 'Original backup changed')
    return journal


def check_owned(journal, recovery=False):
    for item in journal['files']:
        permitted = {item['before'], item['after']} if recovery else {item['after']}
        require(digest_or_none(item['path']) in permitted,
                f'Owned file changed: {item["path"]}')


def temporary_path(state, path, index):
    return Path(path).with_name(f'.project-server-data-{sha(str(state).encode())[:16]}-{index}')


def target_atomic(item, raw):
    """The exact temporary path is owned by the durable journal before creation."""
    path, temporary = safe_path(item['path']), safe_path(item['temporary'])
    created = False
    try:
        with temporary.open('xb') as stream:
            created = True
            stream.write(raw)
            os.fchmod(stream.fileno(), item['mode'])
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fsync_dir(path.parent)
    finally:
        if created and temporary.exists():
            temporary.unlink()
            fsync_dir(temporary.parent)


def plan(manifest, data_dir, state=None):
    manifest, data_dir = Path(manifest).absolute(), Path(data_dir).absolute()
    disjoint(manifest.parent, data_dir, state)
    # Check path ancestors before baseline globbing/merging can traverse them.
    safe_path(data_dir / '.project-path-check')
    manifest_sha, payload = inventory(manifest)
    ident = identity(manifest, data_dir, manifest_sha)
    for name in payload:
        safe_path(data_dir / name)
    for directory, pattern in [('maps', '000*.map'), ('vmaps', '000*.vmtree'),
                               ('mmaps', '000*.mmtile'), ('mmaps', '000.mmap')]:
        for sample in (data_dir / directory).glob(pattern):
            safe_path(sample)
    baseline_check(data_dir)
    pilot = {n: raw for n, kind, raw in payload.donors if kind == 'dbc-delta'}
    merge_server(data_dir, pilot)  # Retain pilot binding/collision validation.
    merged = {}
    # Manifest source order is deterministic. Every donor is applied, including
    # multiple donors for a single target; merge_dbc rejects semantic collisions.
    for name, kind, raw in payload.donors:
        if kind in ('dbc-delta', 'additive-dbc'):
            if kind == 'dbc-delta':
                fields, ids, strings, order = DELTAS[Path(name).name]
            else:
                fields, strings = ADDITIVE_DBC[name]
                ids, order = [r[0] for r in parse_dbc(raw)[1]], False
            base = merged.get(name, (data_dir / name).read_bytes())
            merged[name] = merge_dbc(base, raw, ids, strings, order)
    dependencies = geography_check(payload, data_dir)
    if FACIAL_STYLE_TARGET in payload:
        merged[FACIAL_STYLE_TARGET] = merge_natural_dbc(
            (data_dir / FACIAL_STYLE_TARGET).read_bytes(), payload[FACIAL_STYLE_TARGET])
    outputs = {**payload, **merged}
    entries = []
    for name, raw in sorted(outputs.items()):
        path = safe_path(data_dir / name)
        before = digest_or_none(path)
        if name not in merged:
            require(before is None or before == sha(raw) or
                    before in payload.replacements.get(name, []), f'Server payload collision: {name}')
        entries.append(dict(path=str(path), before=before, after=sha(raw)))
    result = dict(schema=1, identity=ident, files=entries)
    if payload.contract is not None:
        result['dependencies'] = dependencies
    if state is not None:
        state = Path(state).absolute()
        safe_path(state / 'journal.json')
        for directory in (state, *state.parents):
            require(not directory.exists() or directory.is_dir(),
                    f'Not a state directory: {directory}')
        for i, entry in enumerate(entries):
            temporary = safe_path(temporary_path(state, entry['path'], i))
            require(not temporary.exists(), f'Owned temporary exists: {temporary}; use recover')
        if Path(state).exists():
            journal = read_state(state, ident)
            require(journal['phase'] == 'installed', 'Incomplete/retired state: use recover or fresh state')
            check_owned(journal)
            require({i['path']: i['after'] for i in journal['files']} ==
                    {i['path']: i['after'] for i in entries}, 'Installed plan changed')
    return result, outputs


def install(manifest, data_dir, state, offline=False, expected_plan=None):
    require(offline, '--offline is required (server stopped; exclusive access through SQL/install)')
    state = Path(state).absolute()
    current, outputs = plan(manifest, data_dir, state)
    if expected_plan is not None:
        require(current == load_json(Path(expected_plan).read_bytes()),
                'Target/source changed since pre-SQL check')
    if state.exists():
        return dict(status='already-installed')
    durable_mkdir(state)
    with locked(state):
        require(not (state / 'journal.json').exists(), 'State was created by another operation')
        durable_mkdir(state / 'backups')
        entries, directories = [], set()
        for i, entry in enumerate(current['files']):
            item = dict(entry, backup=f'backups/{i}',
                        temporary=str(temporary_path(state, entry['path'], i)))
            path = Path(item['path'])
            require(digest_or_none(path) == item['before'], 'Target changed during preparation')
            item['mode'] = (path.stat().st_mode & 0o777) if path.exists() else 0o644
            if item['before'] is not None:
                raw = path.read_bytes()
                require(sha(raw) == item['before'], 'Target changed while backing up')
                atomic(state / item['backup'], raw)
            for parent in path.parents:
                if parent.exists():
                    break
                directories.add(str(parent))
            entries.append(item)
        journal = dict(schema=1, identity=current['identity'], phase='prepared', files=entries,
                       directories=sorted(directories, key=lambda p: (len(Path(p).parts), p)))
        atomic(state / 'journal.json', json_bytes(journal))
        for directory in journal['directories']:
            durable_mkdir(directory)
        for item in entries:
            require(digest_or_none(item['path']) == item['before'], 'Target changed after preflight')
            if item['after'] != item['before']:
                name = Path(item['path']).relative_to(Path(data_dir).absolute()).as_posix()
                target_atomic(item, outputs[name])
        journal['phase'] = 'installed'
        atomic(state / 'journal.json', json_bytes(journal))
    return dict(status='installed', files=len(entries), state=str(state))


def rollback(manifest, data_dir, state, offline=False, recovery=False):
    require(offline, '--offline is required (server stopped; exclusive access)')
    state = Path(state).absolute()
    disjoint(Path(manifest).absolute().parent, data_dir, state)
    manifest_sha, _ = inventory(manifest)
    ident = identity(manifest, data_dir, manifest_sha)
    journal = read_state(state, ident)
    if journal['phase'] == 'rolled_back':
        for item in journal['files']:
            require(digest_or_none(item['path']) == item['before'], 'Restored file changed')
        return dict(status='already-rolled-back', scope='files-only')
    require(recovery or journal['phase'] == 'installed', 'Interrupted operation: use recover')
    check_owned(journal, recovery=recovery)
    for item in journal['files']:
        safe_path(item['temporary'])
        require(recovery or not Path(item['temporary']).exists(),
                'Interrupted temporary write: use recover')
    with locked(state):
        journal['phase'] = 'rollback_intent'
        atomic(state / 'journal.json', json_bytes(journal))
        for item in journal['files']:
            path = Path(item['path'])
            temporary = safe_path(item['temporary'])
            if temporary.exists():
                temporary.unlink()
                fsync_dir(temporary.parent)
            actual = digest_or_none(path)
            if actual == item['before']:
                # A prior restore may have stopped between replace/unlink and
                # directory fsync. Sync even when its bytes already look restored.
                if path.parent.is_dir():
                    fsync_dir(path.parent)
                continue
            require(actual == item['after'], f'Owned file changed: {path}')
            if item['before'] is None:
                path.unlink()
                fsync_dir(path.parent)
            else:
                target_atomic(item, (state / item['backup']).read_bytes())
        for directory in reversed(journal['directories']):
            path = Path(directory)
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
            if not path.exists():
                # Complete a previous rmdir that may have stopped before fsync.
                # Several nested parents may already be absent after interruption.
                parent = next(p for p in path.parents if p.is_dir())
                fsync_dir(parent)
        journal['phase'] = 'rolled_back'
        atomic(state / 'journal.json', json_bytes(journal))
    return dict(status='rolled-back', scope='files-only')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('validate', 'check', 'install', 'rollback', 'recover'):
        sub = commands.add_parser(command)
        sub.add_argument('--manifest', type=Path, required=True)
        if command != 'validate':
            sub.add_argument('--data-dir', type=Path, required=True)
            sub.add_argument('--state', type=Path, required=command != 'check')
        if command in ('install', 'rollback', 'recover'):
            sub.add_argument('--offline', action='store_true')
        if command == 'install':
            sub.add_argument('--expected-plan', type=Path)
    args = vars(parser.parse_args())
    command = args.pop('command')
    try:
        if command == 'validate':
            digest, payload = inventory(**args)
            result = dict(status='PASS', manifest_sha256=digest, files=len(payload))
        elif command == 'check':
            result, _ = plan(**args)
        elif command == 'recover':
            result = rollback(**args, recovery=True)
        else:
            result = globals()[command](**args)
        print(json.dumps(result, indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f'ERROR: {exc}\n')


if __name__ == '__main__':
    main()
