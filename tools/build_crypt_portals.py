#!/usr/bin/env python3
"""Stage native crypt access under work only; DEV queries are read-only."""
import argparse
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess

from build_crypt_cartography import Builder, ROOT, file_sha, normalize, require, sha

MANIFEST = ROOT / 'tools/crypt_portals.json'
SQL = ROOT / 'data/sql/custom/db_world/turtle_wow_crypt_access.sql'
MEMBER = r'DBFilesClient\AreaTrigger.dbc'
SHAPE = ['entry', 'map', 'x', 'y', 'z', 'radius', 'length', 'width', 'height', 'orientation']
FLOATS = set(SHAPE[2:] + ['size', 'target_position_x', 'target_position_y',
    'target_position_z', 'target_orientation', 'position_x', 'position_y',
    'position_z', 'rotation0', 'rotation1', 'rotation2', 'rotation3'])


def load_manifest():
    return json.loads(MANIFEST.read_text())


def sql_rows(m):
    result = []
    for p in m['portals']:
        ident = p['id']
        result.append(('areatrigger', dict(zip(SHAPE, [ident] + p['trigger']))))
        result.append(('areatrigger_teleport', dict(zip(
            ['ID', 'Name', 'target_map', 'target_position_x', 'target_position_y',
             'target_position_z', 'target_orientation'], [ident, p['name']] + p['destination']))))
        template = dict(entry=ident, type=5, displayId=672, name=p['name'],
                        IconName='', castBarCaption='', unk1='', size=1.6)
        template.update({f'Data{i}': 0 for i in range(24)})
        template.update(m['visual_template'])
        template.update(AIName='', ScriptName='', VerifiedBuild=None)
        result.append(('gameobject_template', template))
        map_id, zone, area, x, y, z, o = p['visual']
        result.append(('gameobject', dict(guid=ident, id=ident, map=map_id,
            zoneId=zone, areaId=area, spawnMask=1, phaseMask=1,
            position_x=x, position_y=y, position_z=z, orientation=o,
            rotation0=0, rotation1=0, rotation2=math.sin(o/2), rotation3=math.cos(o/2),
            spawntimesecs=300, animprogress=255, state=1, ScriptName='',
            VerifiedBuild=None, Comment=p['name'])))
    result.append(('dungeon_access_template', m['access']))
    return result


def literal(value):
    if value is None:
        return 'NULL'
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return str(value)


def equal(column, value):
    # Radius zero selects a box; even a tiny positive value selects a sphere.
    if column == 'radius' and value == 0:
        return '`radius` <=> 0'
    if column in FLOATS:
        return f'ABS(`{column}` - {literal(value)}) <= 0.001'
    if isinstance(value, str):
        return f'BINARY `{column}` <=> BINARY {literal(value)}'
    return f'`{column}` <=> {literal(value)}'


def generate_sql(m):
    # A handler is necessary: MySQL duplicate-key errors alone only roll back
    # the offending statement, not earlier statements in the transaction.
    ids = ','.join(str(p['id']) for p in m['portals'])
    access_id, map_id = m['access']['id'], m['access']['map_id']
    lines = ["-- azerothcore-setup: acceso nativo a Cripta de Karazhan (piloto).",
        '-- Generated from tools/crypt_portals.json; verify with build_crypt_portals.py.',
        '-- Requires existing instance_template(800,0,empty,0) and matching client DBC.',
        '-- Exact reruns are no-ops; any differing owned row fails closed.',
        '-- Run with mysql batch stop-on-error, never --force. No runtime reload here.',
        '-- On failed CALL the transaction is rolled back; remove the helper routine',
        '-- azerothcore_setup_crypt_access after inspecting the collision, before retry.',
        'USE `acore_world`;', 'SET NAMES utf8mb4;', 'DELIMITER $$',
        'CREATE PROCEDURE `azerothcore_setup_crypt_access`()', 'BEGIN',
        '  DECLARE EXIT HANDLER FOR SQLEXCEPTION', '  BEGIN',
        '    ROLLBACK;', '    RESIGNAL;', '  END;', '  START TRANSACTION;',
        f"  IF NOT EXISTS (SELECT 1 FROM `instance_template` WHERE `map`={map_id} AND `parent`=0 AND BINARY `script`=BINARY '' AND `allowMount`=0)",
        f'     OR EXISTS (SELECT 1 FROM `dungeon_access_template` WHERE `map_id`={map_id} AND `id`<>{access_id})',
        f'     OR EXISTS (SELECT 1 FROM `dungeon_access_requirements` WHERE `dungeon_access_id`={access_id})',
        f'     OR EXISTS (SELECT 1 FROM `areatrigger_scripts` WHERE `entry` IN ({ids}))',
        f'     OR EXISTS (SELECT 1 FROM `areatrigger_tavern` WHERE `id` IN ({ids}))',
        f'     OR EXISTS (SELECT 1 FROM `areatrigger_involvedrelation` WHERE `id` IN ({ids}))',
        f'     OR EXISTS (SELECT 1 FROM `gameobject` WHERE `id` IN ({ids}) AND `guid` NOT IN ({ids})) THEN',
        "    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='azerothcore-setup: crypt prerequisite or binding collision';",
        '  END IF;']
    for table, row in sql_rows(m):
        columns = ', '.join(f'`{c}`' for c in row)
        values = ', '.join(literal(v) for v in row.values())
        predicates = '\n      AND '.join(equal(c, v) for c, v in row.items())
        lines += [f'  INSERT INTO `{table}` ({columns})', f'  SELECT {values}',
                  f'  WHERE NOT EXISTS (SELECT 1 FROM `{table}` WHERE {predicates});']
    lines += ['  COMMIT;', 'END$$', 'DELIMITER ;',
              'CALL `azerothcore_setup_crypt_access`();',
              'DROP PROCEDURE `azerothcore_setup_crypt_access`;', '']
    return '\n'.join(lines)


def generate_rollback(m):
    """Remove only these exact owned rows; reject changed or newly bound data."""
    lines = ['USE `acore_world`;', 'SET NAMES utf8mb4;', 'DELIMITER $$',
             'CREATE PROCEDURE `azerothcore_setup_crypt_access_rollback`()', 'BEGIN',
             '  DECLARE EXIT HANDLER FOR SQLEXCEPTION', '  BEGIN',
             '    ROLLBACK;', '    RESIGNAL;', '  END;', '  START TRANSACTION;']
    for table, row in sql_rows(m):
        key = next(iter(row))
        predicates = ' AND '.join(equal(c, v) for c, v in row.items())
        lines += [f'  IF EXISTS (SELECT 1 FROM `{table}` WHERE `{key}`={row[key]})',
                  f'     AND NOT EXISTS (SELECT 1 FROM `{table}` WHERE {predicates}) THEN',
                  "    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Crypt rollback: owned row changed';",
                  '  END IF;']
    lines += [
        '  IF EXISTS (SELECT 1 FROM dungeon_access_requirements WHERE dungeon_access_id=124)',
        '     OR EXISTS (SELECT 1 FROM areatrigger_scripts WHERE entry IN (900800,900801))',
        '     OR EXISTS (SELECT 1 FROM areatrigger_tavern WHERE id IN (900800,900801))',
        '     OR EXISTS (SELECT 1 FROM areatrigger_involvedrelation WHERE id IN (900800,900801))',
        '     OR EXISTS (SELECT 1 FROM gameobject WHERE id IN (900800,900801) AND guid NOT IN (900800,900801)) THEN',
        "    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Crypt rollback: new dependent data';",
        '  END IF;']
    for table, row in reversed(sql_rows(m)):
        key = next(iter(row))
        lines.append(f'  DELETE FROM `{table}` WHERE `{key}`={row[key]};')
    lines += ['  COMMIT;', 'END$$', 'DELIMITER ;',
              'CALL `azerothcore_setup_crypt_access_rollback`();',
              'DROP PROCEDURE `azerothcore_setup_crypt_access_rollback`;', '']
    return '\n'.join(lines)


def parse_dbc(raw):
    require(raw[:4] == b'WDBC' and len(raw) >= 20, 'Invalid WDBC')
    count, fields, size, strings = struct.unpack_from('<4I', raw, 4)
    require(fields == 10 and size == 40 and len(raw) == 20 + count*40 + strings,
            'Unexpected AreaTrigger layout')
    rows = [struct.unpack_from('<2I8f', raw, 20 + i*40) for i in range(count)]
    require(len({r[0] for r in rows}) == count, 'Duplicate trigger IDs')
    return rows, raw[20+count*40:]


def merge_dbc(raw, m):
    rows, strings = parse_dbc(raw)
    require(len(rows) == 1220, 'Expected 1220 native rows')
    require([r[1] for r in rows] == sorted(r[1] for r in rows),
            'Native AreaTrigger rows are not ordered by map')
    native = [raw[20+i*40:20+(i+1)*40] for i in range(len(rows))]
    additions = []
    for p in m['portals']:
        require(p['id'] not in {r[0] for r in rows}, 'Native trigger ID collision')
        additions.append(struct.pack('<2I8f', p['id'], *p['trigger']))
    # Build12340 delimits a contiguous per-map interval, stopping at the first
    # larger map ID. Appending a map0 row after map724 hides it from that scan.
    # Stable sorting raw records preserves native float bits and relative order.
    ordered = sorted(native + additions, key=lambda record: struct.unpack_from('<I', record, 4)[0])
    merged = struct.pack('<4s4I', b'WDBC', 1222, 10, 40, len(strings))
    merged += b''.join(ordered) + strings
    actual, actual_strings = parse_dbc(merged)
    owned = {p['id'] for p in m['portals']}
    require([record for record in ordered if struct.unpack_from('<I', record)[0] not in owned] == native
            and actual_strings == strings, 'Native data or relative order changed')
    for p in m['portals']:
        require(p['id'] in {row[0] for row in client_map_rows(actual, p['trigger'][0])},
                'Portal is outside the client per-map search block')
    return merged


def client_map_rows(rows, map_id):
    """Static build12340 per-map scan contract (not an in-game packet test)."""
    result = []
    for row in rows:
        if row[1] > map_id:
            break
        if row[1] == map_id:
            result.append(row)
    return result


def contains(trigger, point, delta=0):
    """Native sphere / oriented box contract, including optional radius delta."""
    map_id, x, y, z, radius, length, width, height, o = trigger
    pm, px, py, pz = point
    if pm != map_id:
        return False
    dx, dy, dz = px-x, py-y, pz-z
    if radius:
        return dx*dx + dy*dy + dz*dz <= (radius+delta)**2
    # Inverse world rotation, as in IsWithinBox.
    local_x = dx*math.cos(o) + dy*math.sin(o)
    local_y = -dx*math.sin(o) + dy*math.cos(o)
    return (abs(local_x) <= length/2+delta and abs(local_y) <= width/2+delta
            and abs(dz) <= height/2+delta)


def query(sql):
    # Every call is a SELECT in a server-enforced read-only transaction.
    require(sql.lstrip().upper().startswith('SELECT '), 'Read-only query required')
    proc = subprocess.run(['mysql', '--login-path=azeroth-dev', '--batch', '--raw',
        '--skip-column-names', 'acore_world', '-e',
        'START TRANSACTION READ ONLY; ' + sql + '; ROLLBACK;'],
        capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def check_dev(m):
    checks = []
    for table, row in sql_rows(m):
        key = next(iter(row))
        count = int(query(f'SELECT COUNT(*) FROM `{table}` WHERE `{key}`={row[key]}'))
        exact = int(query(f'SELECT COUNT(*) FROM `{table}` WHERE ' +
                         ' AND '.join(equal(c, v) for c, v in row.items())))
        require(count == exact, f'DEV collision: {table}/{row[key]}')
        checks.append(dict(table=table, key=row[key], present=count, identical=exact))
    empty = {
        'areatrigger_scripts': '`entry` IN (900800,900801)',
        'areatrigger_tavern': '`id` IN (900800,900801)',
        'areatrigger_involvedrelation': '`id` IN (900800,900801)',
        'dungeon_access_requirements': '`dungeon_access_id`=124',
        'dungeon_access_template': '`map_id`=800 AND `id`<>124',
        'gameobject': '`id` IN (900800,900801) AND `guid` NOT IN (900800,900801)'}
    for table, where in empty.items():
        require(query(f'SELECT COUNT(*) FROM `{table}` WHERE {where}') == '0',
                f'DEV related collision: {table}')
    require(query("SELECT COUNT(*) FROM instance_template WHERE map=800 AND parent=0 AND script='' AND allowMount=0") == '1', 'Instance prerequisite')
    native = query('SELECT type,displayId,Data1,Data6,AIName,ScriptName FROM gameobject_template WHERE entry=188096')
    require(native == '5\t672\t1\t-1', 'Native portal template configuration drift')
    return dict(rows=checks, related_collisions=0, instance_template_preserved=True,
                native_template_188096=native, max_access_id=query('SELECT MAX(id) FROM dungeon_access_template'))


def check_sources(m):
    """Recheck project/core/module source namespaces, excluding this feature SQL."""
    pattern = r'\b(' + '|'.join(str(p['id']) for p in m['portals']) + r')\b'
    roots = [ROOT / 'data', Path('/home/dev/azerothcore')]
    command = ['rg', '-n', '--glob', '*.sql', '--glob', '*.cpp', '--glob', '*.h',
               pattern, *map(str, roots)]
    proc = subprocess.run(command, capture_output=True, text=True)
    require(proc.returncode in (0, 1), f'Source scan failed: {proc.stderr}')
    hits = [line for line in proc.stdout.splitlines() if not line.startswith(str(SQL) + ':')]
    require(not hits, 'Source namespace collision: ' + '\n'.join(hits))
    return dict(command=command, collisions=hits, excluded_owned_sql=str(SQL))


class PortalBuilder(Builder):
    def build_portals(self, m):
        inputs = m['inputs']
        baseline = ROOT / inputs['baseline']
        require(file_sha(baseline) == inputs['baseline_sha256'], 'Approved baseline mismatch')
        originals = {}
        for line in self.run('list', baseline).decode().splitlines():
            name, size = line.rsplit('\t', 1)
            if name.startswith('('):
                continue
            require(not name.startswith('File'), 'Unresolved archive name')
            data = self.extract(baseline, name)
            require(len(data) == int(size), 'Short extraction')
            self.put(name, data)
            originals[normalize(name)] = sha(data)
        require(len(originals) == inputs['baseline_resources'], 'Expected 68 baseline resources')
        require(normalize(MEMBER) not in originals, 'Baseline unexpectedly owns AreaTrigger')
        raw = self.extract(Path(inputs['wotlk_archive']), MEMBER)
        require(sha(raw) == inputs['wotlk_dbc_sha256'], 'WotLK source mismatch')
        server = Path(inputs['server_dbc']).read_bytes()
        # Accept the exact previous owned r4 output only as a migration input.
        # It must never be emitted again: its appended map0 record is hidden.
        _, native_strings = parse_dbc(raw)
        previous_owned = (struct.pack('<4s4I', b'WDBC', 1222, 10, 40, len(native_strings))
                          + raw[20:20+1220*40]
                          + b''.join(struct.pack('<2I8f', p['id'], *p['trigger']) for p in m['portals'])
                          + native_strings)
        require(server in (raw, previous_owned, merge_dbc(raw, m)),
                'Server DBC differs from both the native and owned merged versions')
        turtle = self.extract(Path(m['provenance']['turtle_archive']), MEMBER)
        require(sha(turtle) == m['provenance']['turtle_dbc_sha256'], 'Turtle source mismatch')
        turtle_rows = {r[0]: list(r) for r in parse_dbc(turtle)[0]}
        for field in ('turtle_entrance', 'turtle_exit'):
            row = m['provenance'][field]
            require(turtle_rows[row[0]] == row, 'Turtle provenance mismatch')
        # Probe by name, never rely on incomplete external listfiles. Any custom
        # override must be researched explicitly; older stock DBCs are expected.
        audit = []
        snapshots = sorted(p for p in (self.w335 / 'Data').rglob('*')
                           if p.is_file() and p.suffix.lower() == '.mpq')
        require(snapshots, 'Missing reference snapshot')
        stock = {'common', 'common-2', 'expansion', 'lichking', 'patch', 'patch-2',
                 'patch-3', 'locale-enus', 'locale-eses', 'expansion-locale-enus',
                 'expansion-locale-eses', 'lichking-locale-enus', 'lichking-locale-eses',
                 'patch-enus', 'patch-enus-2', 'patch-enus-3',
                 'patch-eses', 'patch-eses-2', 'patch-eses-3'}
        coordinated = [ROOT / 'work/client-overlay-r3' / r for r in inputs['z_copies']]
        for archive in snapshots + coordinated:
            data = self.extract(archive, MEMBER, optional=True)
            if data is not None:
                require(archive.stem.lower() in stock, f'Unresearched AreaTrigger override: {archive}')
                require(not ({900800, 900801} & {r[0] for r in parse_dbc(data)[0]}),
                        'Snapshot trigger collision')
                if archive.stem.lower().endswith('-3') and archive.parent.name in ('enUS', 'esES'):
                    require(data == raw, 'Effective locale DBC differs')
            audit.append(dict(archive=str(archive), area_trigger_sha256=sha(data) if data else None))
        display = Path('/home/dev/azerothcore/env/dist/bin/dbc/GameObjectDisplayInfo.dbc').read_bytes()
        n, fields, size, strings = struct.unpack_from('<4I', display, 4)
        require(display[:4] == b'WDBC' and fields >= 2 and size == fields*4 and
                len(display) == 20+n*size+strings, 'Invalid display DBC')
        ids = [struct.unpack_from('<2I', display, 20+i*size) for i in range(n)]
        offset = next(r[1] for r in ids if r[0] == 672)
        block = display[20+n*size:]
        model = block[offset:block.index(b'\0', offset)].decode()
        require(model.lower().replace('/', '\\') == r'world\generic\activedoodads\instanceportal\instanceportal.mdx', 'Native display model drift')
        dev = check_dev(m)
        source_collision_audit = check_sources(m)
        merged = merge_dbc(raw, m)
        self.put(MEMBER, merged)
        sql = generate_sql(m)
        require(SQL.read_text() == sql, 'Tracked SQL differs from manifest; update via apply_patch')
        (self.out / SQL.name).write_text(sql)
        (self.out / 'rollback_crypt_access.sql').write_text(generate_rollback(m))
        server_out = self.out / 'server/dbc/AreaTrigger.dbc'
        server_out.parent.mkdir(parents=True)
        server_out.write_bytes(merged)
        entries = sorted(self.payload.values(), key=lambda entry: normalize(entry[0]))
        listing = self.out / 'patch.list'
        listing.write_text(''.join(f'{path}|{name}\n' for name, path in entries))
        final = self.out / 'Data/patch-T.MPQ'
        final.parent.mkdir()
        self.run('create', final, listing)
        roundtrip = []
        for i, (name, path) in enumerate(entries):
            dest = self.out / 'roundtrip' / str(i)
            dest.parent.mkdir(exist_ok=True)
            self.run('extract-one', final, name, dest)
            require(dest.read_bytes() == path.read_bytes(), f'MPQ roundtrip failed: {name}')
            if normalize(name) in originals:
                require(file_sha(dest) == originals[normalize(name)], 'Baseline resource changed')
            roundtrip.append(dict(member=name, sha256=file_sha(dest)))
        listed = {normalize(line.rsplit('\t', 1)[0]) for line in
                  self.run('list', final).decode().splitlines() if not line.startswith('(')}
        require(listed == set(self.payload) and len(listed) == 69, 'Expected 69 r4 resources')
        for relative, expected in inputs['z_copies'].items():
            source = ROOT / 'work/client-overlay-r3' / relative
            require(file_sha(source) == expected, 'Coordinated Z hash mismatch')
            dest = self.out / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
            require(file_sha(dest) == expected, 'Z copy mismatch')
        client_rows = {r[0]: list(r) for r in parse_dbc(merged)[0] if r[0] in (900800, 900801)}
        for p in m['portals']:
            packed = list(struct.unpack('<2I8f', struct.pack('<2I8f', p['id'], *p['trigger'])))
            require(client_rows[p['id']] == packed, 'Client trigger mismatch')
            require(server_out.read_bytes() == merged, 'Client/server DBC mismatch')
            # At world coordinates near 11000, one float32 ULP is 0.0009765625.
            require(all(abs(a-b) <= 0.001 for a, b in zip(packed, [p['id']] + p['trigger'])), 'SQL/DBC float mismatch')
        for path, info in self.archives.items():
            require(file_sha(Path(path)) == info['sha256'], f'Input changed: {path}')
        require(Path(inputs['server_dbc']).read_bytes() == server, 'Server input changed')
        report = dict(status='staged only; no deployment or gameplay test',
            patch_sha256=file_sha(final), dbc_sha256=sha(merged), sql_sha256=sha(sql.encode()),
            manifest_sha256=file_sha(MANIFEST), baseline_sha256=inputs['baseline_sha256'],
            baseline_resources_preserved=68, payload_resources=69, rows_before=1220, rows_after=1222,
            original_record_bytes_preserved=True, original_string_bytes_preserved=True,
            native_relative_order_preserved=True, sorted_by_map=True,
            client_search_blocks={str(p['trigger'][0]): [r[0] for r in client_map_rows(
                parse_dbc(merged)[0], p['trigger'][0])] for p in m['portals']},
            client_rows=client_rows, server_rows=client_rows, sql_rows=sql_rows(m),
            sql_rows_count=9, client_server_sql_match=True, native_display=dict(id=672, model=model),
            coordinated_z=inputs['z_copies'], dev_readonly=dev, snapshot_override_audit=audit,
            source_collision_audit=source_collision_audit,
            sources=self.sources, archives=self.archives, roundtrip=roundtrip,
            limitations=['Reference snapshot is not the active client.',
                'Walking, portal alignment, level54/55, group/solo and corpse return require in-game testing.',
                'SQL generated and reviewed only; not executed, including rollback handler.'])
        (self.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({k: report[k] for k in ('patch_sha256', 'dbc_sha256', 'sql_sha256', 'payload_resources', 'sql_rows_count')}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'work/client-overlay-r4.1')
    parser.add_argument('--sql-only', action='store_true', help='Print canonical SQL; write no files')
    args = parser.parse_args()
    m = load_manifest()
    if args.sql_only:
        print(generate_sql(m), end='')
        return
    PortalBuilder(args.output.resolve(), Path('/home/dev/wow-335'),
                  Path('/home/dev/wow-turtle'), ROOT / 'work/client-overlay-r3').build_portals(m)


if __name__ == '__main__':
    main()
