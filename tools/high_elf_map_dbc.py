#!/usr/bin/env python3
"""Offline Map0 high-elf geographic DBC candidates. No deployment operations.

    python3 tools/high_elf_map_dbc.py

Builds server/enUS/esES DBCs and compact, relocatable row deltas under work/.
Every build queries DEV's three DBC overlays read-only and scans relevant SQL.
An existing output is accepted only when every byte matches (idempotent rerun).
The pure apply_delta API accepts identical owned rows, rejects ID/natural-key/
exploration-bit conflicts, and preserves every pre-existing row and string byte.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import tempfile

from dbc_write import write_dbc_bytes

ROOT = Path(__file__).resolve().parent.parent
TABLES = {'AreaTable': (25, 36), 'WMOAreaTable': (20, 28),
          'WorldMapArea': (8, 11)}
SQL_TABLES = {'AreaTable': 'areatable_dbc', 'WMOAreaTable': 'wmoareatable_dbc',
              'WorldMapArea': 'worldmaparea_dbc'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse(data, fields):
    require(len(data) >= 20 and data[:4] == b'WDBC', 'Invalid WDBC header')
    n, f, size, ns = struct.unpack_from('<4I', data, 4)
    require(f == fields and size == f * 4 and len(data) == 20 + n * size + ns,
            'Invalid WDBC schema/length')
    rows = [list(r) for r in struct.iter_unpack('<%dI' % f, data[20:20+n*size])]
    require(len({r[0] for r in rows}) == n, 'Duplicate record ID')
    strings = data[20+n*size:]
    require(strings and strings[0] == 0 and strings[-1] == 0, 'Invalid string block')
    return rows, strings


def string_at(strings, offset):
    require(0 <= offset < len(strings), 'String offset out of bounds')
    # DBC string suffix sharing is valid: no requirement for a preceding NUL.
    end = strings.find(b'\0', offset)
    require(end >= 0, 'Unterminated string')
    return strings[offset:end]


def string_fields(table):
    return [3] if table == 'WorldMapArea' else list(range(11, 27))


def semantic(table, row, strings):
    values = list(row)
    for col in string_fields(table):
        values[col] = string_at(strings, row[col])
    return values


def mapping(config, key):
    return {int(k): v for k, v in config[key].items()}


def make_deltas(config, sources):
    """Convert 25/20/8-field Turtle schemas, retaining raw float/string bytes."""
    areas, bits = mapping(config, 'area_ids'), mapping(config, 'explore_flags')
    require(config['map_id'] == 0, 'Only native Map0 is supported')
    require(set(areas) == set(bits) and len(set(areas.values())) == len(areas),
            'Invalid area allocation')
    require(len(set(bits.values())) == len(bits) and
            all(0 < b < 4096 for b in bits.values()), 'Invalid exploration allocation')
    source_rows, _ = parse(sources['AreaTable'], 25)
    closure = set(config['roots'])
    while True:
        expanded = closure | {r[0] for r in source_rows if r[2] in closure}
        if expanded == closure:
            break
        closure = expanded
    require(closure == set(areas), 'Source area closure differs from reservation')
    result, evidence = {}, {'areas': [], 'excluded_wmo': [], 'wmo_group_mappings': []}
    group_mappings = mapping(config, 'wmo_group_mappings') if 'wmo_group_mappings' in config else {}
    require(set(group_mappings) <= set(mapping(config, 'wmo_ids')), 'Unallocated WMO group mapping')
    for table, (old, new) in TABLES.items():
        rows, strings = parse(sources[table], old)
        sb, out = bytearray(b'\0'), []

        def add(offset):
            value = string_at(strings, offset)
            if not value:
                return 0
            pos = len(sb)
            sb.extend(value + b'\0')
            return pos

        ids = areas if table == 'AreaTable' else mapping(
            config, 'wmo_ids' if table == 'WMOAreaTable' else 'worldmap_ids')
        require(len(set(ids.values())) == len(ids), 'Duplicate destination allocation')
        found = set()
        for row in rows:
            if table == 'WMOAreaTable' and row[10] in areas:
                if row[0] in config['excluded_inherited_wmo_ids']:
                    require(row[1] == 4772 and row[2] == 1 and row[10] == 3881,
                            'Unexpected excluded WMO identity')
                    evidence['excluded_wmo'].append(row[:11])
                    continue
                require(row[0] in ids, 'Unallocated source WMO row')
            if table == 'WorldMapArea' and row[2] in areas:
                require(row[0] in ids, 'Unallocated source WorldMapArea row')
            if row[0] not in ids:
                continue
            found.add(row[0])
            target = [0] * new
            if table == 'AreaTable':
                require(row[1] == 0 and (row[2] == 0 or row[2] in areas),
                        'Area outside Map0/parent closure')
                # The source has one legacy liquid field, not four WotLK IDs.
                require(row[21] == 0, 'Nonzero legacy liquid requires explicit conversion')
                target[:11] = row[:11]
                target[2] = areas.get(row[2], 0)
                target[3] = bits[row[0]]
                target[27:29] = [row[19], row[20]]
                target[33:36] = row[22:25]
                evidence['areas'].append(dict(source=row[0], destination=ids[row[0]],
                                              parent=target[2], explore_flag=target[3],
                                              name=string_at(strings, row[11]).decode('utf-8')))
            elif table == 'WMOAreaTable':
                require(row[1] in (6000, 6001, 6002) and row[10] in areas,
                        'Unexpected custom WMO root/area')
                target[:11] = row[:11]
                target[10] = areas[row[10]]
                target[27] = row[19]
                if row[0] in group_mappings:
                    fix = group_mappings[row[0]]
                    require([ids[row[0]], *row[1:4]] ==
                            [fix['target_id'], fix['root_id'], fix['name_set'], fix['source_group']],
                            'WMO group mapping source identity changed')
                    target[3] = fix['target_group']
                    evidence['wmo_group_mappings'].append(dict(source_id=row[0], **fix))
            else:
                require(row[1] == 0 and row[2] in areas, 'WorldMapArea outside Map0')
                bounds = struct.unpack('<4f', struct.pack('<4I', *row[4:8]))
                require(all(math.isfinite(v) for v in bounds) and
                        bounds[0] != bounds[1] and bounds[2] != bounds[3],
                        'Invalid worldmap bounds')
                target[:8] = row[:8]
                target[2], target[3] = areas[row[2]], add(row[3])
                target[8] = 0xffffffff  # native map, no dungeon/parent override
            target[0] = ids[row[0]]
            if table != 'WorldMapArea':
                target[11:19] = [add(o) for o in row[11:19]]
                # Existing source esES, or unchanged English fallback; no translation.
                if not target[17]:
                    target[17] = target[11]
            out.append(target)
        require(found == set(ids), f'Missing source records: {table}')
        result[table] = write_dbc_bytes(new, out, bytes(sb))
    require({r[0] for r in evidence['excluded_wmo']} ==
            set(config['excluded_inherited_wmo_ids']), 'Missing inherited WMO exclusions')
    return result, evidence


def validate_placed_wmo(delta, placed, group_mappings=()):
    """Exact metadata keys only; no invented coverage for source-less groups.

    `placed` is a sequence of (MOHD root ID, MODF nameSet, MOGP group IDs).
    A -1 row is retained metadata, never a fallback for a missing exact group.
    """
    rows, _ = parse(delta, 28)
    roots = {r[1] for r in rows}
    checked = set()
    required = {fix['target_id']: fix for fix in group_mappings}
    families = {}
    for root, name_set, groups in placed:
        families.setdefault((root, name_set), set()).update(groups)
    for (root, name_set), groups in families.items():
        if root not in roots:
            continue
        candidates = [r for r in rows if r[1:3] == [root, name_set]]
        require(candidates, f'Placed WMO nameSet has no source metadata: {root}/{name_set}')
        for row in candidates:
            if row[0] in required:
                fix = required[row[0]]
                require(row[1:4] == [fix['root_id'], fix['name_set'], fix['target_group']] and
                        row[3] in groups, f'Placed WMO exact group mismatch: row {row[0]}')
            if row[3] == 0xffffffff or row[3] in groups:
                checked.add(row[0])
    require(set(required) <= checked, 'Mapped WMO metadata has no matching placed root/nameSet/group')
    return {'checked_rows': sorted(checked), 'exact_lookup': True,
            'unused_source_rows': sorted({r[0] for r in rows} - checked),
            'unused_groups_without_source_metadata_require_rows': False}


def validate_assets_wmo(delta, directory, config=None):
    """Read only manifest-pinned final ADT/WMO assets, including MODF nameSet."""
    from adt_refs import chunk, name_offsets
    from high_elf_map_assets import wmo_chunks
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    require(manifest['asset_closure_complete'] and not manifest['blockers'], 'Final assets not closed')
    norm = lambda name: name.replace('\\', '/').lower()
    files = {norm(f['path']): f for f in manifest['files']}
    resources = {norm(r['target']): r for r in manifest['resources'] if r['kind'] == 'wmo'}

    def read(name):
        spec = files[norm(name)]
        data = (directory / 'files' / spec['path'].replace('\\', '/')).read_bytes()
        require(sha(data) == spec['sha256'], 'Final asset hash changed: ' + name)
        return data

    placed = set()
    for tile in manifest['tiles']:
        data = read(tile['target'])
        _, names = chunk(data, 5, b'OMWM')
        _, indices = chunk(data, 6, b'DIWM')
        _, records = chunk(data, 8, b'FDOM')
        starts = name_offsets(names)
        require(len(indices) % 4 == 0 and len(records) % 64 == 0, 'Invalid final MODF/MWID')
        offsets = [v[0] for v in struct.iter_unpack('<I', indices)]
        for pos in range(0, len(records), 64):
            index = struct.unpack_from('<I', records, pos)[0]
            require(index < len(offsets) and offsets[index] in starts, 'Invalid final WMO name index')
            name = starts[offsets[index]].decode('latin1')
            resource = resources[norm(name)]
            if resource['status'] == 'native-reuse':
                continue
            root = struct.unpack_from('<I', dict(wmo_chunks(read(name)))['MOHD'], 32)[0]
            name_set = struct.unpack_from('<H', records, pos + 60)[0]
            groups = []
            for i, group in enumerate(resource['groups']):
                raw = read(name[:-4] + f'_{i:03}.wmo')
                gid = struct.unpack_from('<I', dict(wmo_chunks(raw))['MOGP'], 56)[0]
                require(gid == group['group_id'], 'Final MOGP identity changed')
                groups.append(gid)
            placed.add((root, name_set, tuple(groups)))
    if config is None:
        config = json.loads((ROOT / 'tools/high-elf-map.json').read_text())
    report = validate_placed_wmo(delta, placed, config.get('wmo_group_mappings', {}).values())
    report['assets_manifest_sha256'] = sha((directory / 'manifest.json').read_bytes())
    report['placed_keys'] = sorted([root, ns, list(groups)] for root, ns, groups in placed)
    return report


def apply_delta(table, baseline, delta):
    """Pure, collision-guarded additive merge. Does not touch any filesystem."""
    fields = TABLES[table][1]
    rows, strings = parse(baseline, fields)
    additions, ds = parse(delta, fields)
    by_id = {r[0]: semantic(table, r, strings) for r in rows}
    sb, pending = bytearray(strings), []
    for row in additions:
        value = semantic(table, row, ds)
        if row[0] in by_id:
            require(by_id[row[0]] == value, f'{table} ID collision: {row[0]}')
        for other in rows + pending:
            if other[0] == row[0]:
                continue
            if table == 'AreaTable':
                require(other[3] != row[3], f'AreaTable exploreFlag collision: {row[3]}')
            elif table == 'WMOAreaTable':
                require(other[1:4] != row[1:4], f'WMO natural-key collision: {row[1:4]}')
            else:
                require(other[1:3] != row[1:3], f'WorldMapArea map/area collision: {row[1:3]}')
                require(string_at(bytes(sb), other[3]) != value[3],
                        'WorldMapArea internal-name collision')
        if row[0] in by_id:
            continue
        relocated = list(row)
        for col in string_fields(table):
            text = value[col]
            relocated[col] = len(sb) if text else 0
            if text:
                sb.extend(text + b'\0')
        pending.append(relocated)
        by_id[row[0]] = value
    if not pending:
        return baseline
    merged = write_dbc_bytes(fields, rows + pending, bytes(sb))
    # Appending retains physical ordering of all native records as well as bytes.
    require(merged[20:20+len(rows)*fields*4] == baseline[20:20+len(rows)*fields*4]
            and bytes(sb).startswith(strings), 'Native bytes changed')
    return merged


def extract(archive, member):
    """Direct lookup; a missing member is the only accepted extraction failure."""
    with tempfile.TemporaryDirectory(prefix='high-elf-dbc-') as tmp:
        output = Path(tmp) / 'member.dbc'
        run = subprocess.run([str(ROOT / 'tools/mpq'), 'extract-one', str(archive),
                              member, str(output)], capture_output=True, check=False)
        if run.returncode:
            require(b'file not found in archive' in run.stderr,
                    f'Cannot read archive {archive}: {run.stderr.decode()}')
            return None
        return output.read_bytes()


def resolve_regular(config, locale, table):
    """Regular profile first; official stock chain supplies non-overridden DBCs.

    Never uses snapshot custom Z/M/N/F/T as a fallback to regular delivery.
    Root custom duplicates of localized tables are rejected, not guessed around.
    """
    regular = ROOT / config['regular_directory']
    stock = ROOT / config['stock_directory']
    member = 'DBFilesClient\\' + table + '.dbc'
    custom = [regular / locale / f'patch-{locale}-Z.MPQ',
              regular / 'patch-Z.mpq', regular / 'patch-T.MPQ', regular / 'patch-S.MPQ']
    candidates = []
    for archive in custom:
        require(archive.is_file(), f'Missing regular profile archive: {archive}')
        data = extract(archive, member)
        if data is not None:
            candidates.append((data, archive))
    require(len(candidates) <= 1, f'Ambiguous regular root/locale DBC: {table}')
    if candidates:
        return candidates[0]
    names = ([f'patch-{locale}-3.MPQ', f'patch-{locale}-2.MPQ', f'patch-{locale}.MPQ',
              f'lichking-locale-{locale}.MPQ', f'expansion-locale-{locale}.MPQ',
              f'locale-{locale}.MPQ'])
    # Filesystem spelling differs for the stock Spanish distribution.
    available = {p.name.lower(): p for p in (stock / locale).iterdir() if p.is_file()}
    for name in names:
        archive = available.get(name.lower())
        if archive:
            data = extract(archive, member)
            if data is not None:
                return data, archive
    raise ValueError(f'Missing stock locale baseline: {locale}/{table}')


def mysql_overlays(login_path):
    """Only SELECT statements; return full rows/columns as auditable evidence."""
    result = {}
    for table, sql_table in SQL_TABLES.items():
        schema = subprocess.run(['mysql', f'--login-path={login_path}', '--batch',
                                 '--skip-column-names', 'acore_world', '-e',
                                 f'SHOW COLUMNS FROM {sql_table}'],
                                capture_output=True, text=True, check=True)
        columns = [line.split('\t')[0] for line in schema.stdout.splitlines()]
        require(columns and columns[0] == 'ID', f'Invalid SQL schema: {sql_table}')
        run = subprocess.run(['mysql', f'--login-path={login_path}', '--batch',
                              '--skip-column-names', 'acore_world', '-e',
                              f'SELECT * FROM {sql_table} ORDER BY ID'],
                             capture_output=True, text=True, check=True)
        lines = run.stdout.splitlines()
        require(all(len(line.split('\t')) == len(columns) for line in lines),
                f'Invalid SQL row width: {sql_table}')
        result[table] = {'columns': columns,
                         'rows': [dict(zip(columns, line.split('\t'))) for line in lines],
                         'query_sha256': sha(run.stdout.encode())}
    return result


def guard_overlays(overlays, deltas):
    """SQL overrides replace file records. Fail even on same-ID SQL ownership."""
    for table, evidence in overlays.items():
        rows, strings = parse(deltas[table], TABLES[table][1])
        for sql in evidence['rows']:
            for row in rows:
                require(int(sql['ID']) != row[0], f'{table} SQL ID collision: {row[0]}')
                if table == 'AreaTable':
                    require(int(sql['AreaBit']) != row[3], 'SQL exploreFlag collision')
                    require(int(sql['ParentAreaID']) != row[0], 'SQL area parent reference')
                elif table == 'WMOAreaTable':
                    key = [int(sql[c]) & 0xffffffff for c in ('WMOID', 'NameSetID', 'WMOGroupID')]
                    require(key != row[1:4], 'SQL WMO natural-key collision')
                else:
                    require([int(sql['MapID']), int(sql['AreaID'])] != row[1:3],
                            'SQL WorldMapArea map/area collision')
                    require(sql['AreaName'].encode() != string_at(strings, row[3]),
                            'SQL WorldMapArea internal-name collision')


def audit_sql_sources(config, deltas):
    """Conservative reservation scan in SQL files referencing the three tables.

    Hits fail closed for manual investigation, including retired SQL. Numeric
    tokens are checked only in statements mentioning the relevant DBC table:
    unrelated item/spawn namespaces do not reserve AreaTable IDs.
    """
    reservations = {}
    for table, data in deltas.items():
        rows, _ = parse(data, TABLES[table][1])
        reservations[table] = {r[0] for r in rows}
        if table == 'AreaTable':
            reservations[table].update(r[3] for r in rows)
        if table == 'WMOAreaTable':
            reservations[table].update(r[1] for r in rows)
    evidence = []
    roots = [ROOT / 'data/sql', Path(config['core_directory']) / 'data/sql',
             Path(config['core_directory']) / 'modules']
    for root in roots:
        require(root.is_dir(), f'Missing SQL audit root: {root}')
        for path in sorted(root.rglob('*.sql')):
            data = path.read_bytes()
            lower = data.lower()
            tables = [t for t, name in SQL_TABLES.items() if name.encode() in lower]
            if not tables:
                continue
            # Ignore comments: schema/history comments are not row allocations.
            text = re.sub(r'/\*.*?\*/|--[^\n]*|#[^\n]*', '', data.decode('utf-8'),
                          flags=re.S)
            # Keep quoted semicolons inside their statement.
            tokens = re.findall(r"'(?:''|\\.|[^'\\])*'|\"(?:\"\"|\\.|[^\"\\])*\"|`[^`]*`|;|[^;'\"`]+",
                                text, flags=re.S)
            statements, current = [], []
            for token in tokens:
                current.append(token)
                if token == ';':
                    statements.append(''.join(current))
                    current = []
            statements.append(''.join(current))
            hits = {}
            for table in tables:
                relevant = '\n'.join(s for s in statements
                                     if SQL_TABLES[table] in s.lower())
                numbers = {int(n) for n in re.findall(r'(?<![\w.])\d+(?![\w.])', relevant)}
                hits[table] = sorted(numbers & reservations[table])
            require(not any(hits.values()), f'Reserved identifiers in SQL {path}: {hits}')
            evidence.append({'path': str(path), 'sha256': sha(data), 'tables': tables})
    return evidence


def build(config, login_path='azeroth-dev', output=None):
    sources, inputs = {}, {}
    for table in TABLES:
        path = ROOT / config['source_directory'] / (table + '.dbc')
        data = path.read_bytes()
        require(sha(data) == config['source_sha256'][table], f'Source hash changed: {path}')
        sources[table] = data
        inputs['source/' + table] = {'path': str(path), 'sha256': sha(data)}
    deltas, report = make_deltas(config, sources)
    report['placed_wmo_validation'] = validate_assets_wmo(
        deltas['WMOAreaTable'], ROOT / config['assets_directory'])
    overlays = mysql_overlays(login_path)
    guard_overlays(overlays, deltas)
    report['sql_overlays'] = overlays
    report['sql_sources'] = audit_sql_sources(config, deltas)
    report['limits'] = config['limits']
    report['map_id'] = 0
    report['allocations'] = {key: config[key] for key in
                             ('area_ids', 'explore_flags', 'wmo_ids', 'worldmap_ids')}
    report['baselines'] = {}
    artifacts = {}
    for profile in ('server', 'enUS', 'esES'):
        report['baselines'][profile] = {}
        for table in TABLES:
            if profile == 'server':
                path = Path(config['server_directory']) / (table + '.dbc')
                baseline = path.read_bytes()
            else:
                baseline, path = resolve_regular(config, profile, table)
            inputs[profile + '/' + table] = {'path': str(path), 'sha256': sha(baseline)}
            merged = apply_delta(table, baseline, deltas[table])
            require(apply_delta(table, merged, deltas[table]) == merged, 'Non-idempotent merge')
            rows, strings = parse(baseline, TABLES[table][1])
            actual, _ = parse(merged, TABLES[table][1])
            report['baselines'][profile][table] = {
                'rows_before': len(rows), 'rows_after': len(actual),
                'native_rows_byteexact': True, 'native_strings_byteexact': True,
                'native_strings_sha256': sha(strings)}
            artifacts[f'{profile}/DBFilesClient/{table}.dbc'] = merged
    for table, data in deltas.items():
        artifacts[f'deltas/{table}.dbc'] = data
    report['inputs'] = inputs
    report['configuration_sha256'] = sha(json.dumps(config, sort_keys=True).encode())
    report['artifacts'] = {name: {'sha256': sha(data), 'size': len(data)}
                           for name, data in artifacts.items()}
    artifacts['report.json'] = (json.dumps(report, indent=2, ensure_ascii=False) + '\n').encode()
    destination = Path(output) if output else ROOT / config['output_directory']
    # Candidate output is confined to work/, including when paths contain symlinks.
    destination = destination.resolve()
    require(destination.is_relative_to((ROOT / 'work').resolve()) and
            destination != (ROOT / 'work').resolve(), 'Output must be a subdirectory of work/')
    if destination.exists():
        existing = {str(p.relative_to(destination)): p.read_bytes()
                    for p in destination.rglob('*') if p.is_file()}
        require(existing == artifacts, f'Existing candidate differs: {destination}')
    else:
        for name, data in artifacts.items():
            path = destination / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'tools/high-elf-map.json')
    parser.add_argument('--login-path', default='azeroth-dev')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = build(json.loads(args.config.read_text()), args.login_path, args.output)
    print(json.dumps({'areas': report['areas'], 'baselines': report['baselines'],
                      'limits': report['limits']}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
