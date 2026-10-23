#!/usr/bin/env python3
"""Build an isolated native ForestTroll patch from pinned, read-only clients.

python3 tools/build_forest_troll_skins.py --output work/forest-troll-skins-r1
Optional --publish copies only Data/patch-S.MPQ, report.json, SHA256SUMS and
the two canonical SQL files to their owned setup paths (never installs them).
No work/audit JSON or loose extracted DBC is an input. Failed SQL CALLs roll
back data but leave their helper procedure/temp table for explicit inspection
and cleanup before retrying; never use mysql --force to apply these scripts.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'tools/forest-troll-skins.json'
MPQ = ROOT / 'tools/mpq'
COLS = ('Id', 'Race', 'Gender', 'GenType', 'TexturePath1', 'TexturePath2',
        'TexturePath3', 'Flags', 'Type', 'Color')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_dbc(raw):
    require(len(raw) >= 20, 'Truncated DBC header')
    magic, n, fields, size, ns = struct.unpack_from('<4s4I', raw)
    require(magic == b'WDBC' and fields == 10 and size == 40,
            'Expected ten-field CharSections WDBC')
    require(ns > 0 and len(raw) == 20 + n * size + ns, 'Invalid DBC lengths')
    rows = [struct.unpack_from('<10I', raw, 20 + i * size) for i in range(n)]
    strings = raw[20 + n * size:]
    require(strings[0] == 0, 'Missing empty DBC string')
    return rows, strings


def text(strings, offset):
    require(0 <= offset < len(strings), 'DBC string offset outside block')
    end = strings.find(b'\0', offset)
    require(end >= 0, 'Unterminated DBC string')
    return strings[offset:end].decode('utf-8')


def decode(row, strings, schema='335'):
    require(len(row) == 10 and schema in ('335', 'turtle'), 'Unknown schema')
    if schema == 'turtle':
        ident, race, sex, base, var, color, a, b, c, flags = row
    else:
        ident, race, sex, base, a, b, c, flags, var, color = row
    return (ident, race, sex, base, text(strings, a), text(strings, b),
            text(strings, c), flags, var, color)


def key(row):
    # Flags are eligibility, NOT part of the native lookup key.
    return row[1], row[2], row[3], row[8], row[9]


def select_source(rows, strings):
    selected = [decode(r, strings, 'turtle') for r in rows
                if r[1] == 8 and r[2] in (0, 1) and r[3] in (0, 1, 4)
                and 6 <= r[5] <= 11 and r[9] == 0]
    expected = {(8, sex, base, var, color)
                for sex in (0, 1) for color in range(6, 12)
                for base in (0, 1, 4)
                for var in (range(5 + sex) if base == 1 else (0,))}
    require(len(selected) == 90 and {key(r) for r in selected} == expected,
            'Incomplete or duplicate source body/face/underwear family')
    for r in selected:
        sex = ('Male', 'Female')[r[2]]
        for name in r[4:7]:
            if name:
                require(re.fullmatch(r'Character\\Troll\\' + sex + r'\\ForestTroll'
                                     + sex + r'[A-Za-z0-9_]+\.blp', name) is not None,
                        'Unexpected source texture: ' + name)
        expected_slots = (True, r[3] == 1 or (r[3] == 4 and r[2] == 1), False)
        require(tuple(bool(n) for n in r[4:7]) == expected_slots,
                'Missing or unexpected surface')
    return sorted(selected, key=key)


def relocated(name, namespace):
    if not name:
        return ''
    return name.replace('Character\\Troll', namespace, 1)


def make_delta(selected, manifest):
    t = manifest['target']
    require(t['id_first'] == 20000 and t['id_last'] == 20089
            and t['color_offset'] == 12 and t['flags'] == 0x11
            and t['namespace'] == 'Character\\Custom\\TurtleForestTroll',
            'Unsupported allocation/flags/namespace decision')
    return [(t['id_first'] + i, *r[1:4],
             *(relocated(n, t['namespace']) for n in r[4:7]),
             t['flags'], r[8], r[9] + t['color_offset'])
            for i, r in enumerate(selected)]


def merge(native, strings, delta):
    ids = [r[0] for r in native]
    require(len(ids) == len(set(ids)), 'Duplicate baseline IDs')
    require(len({r[0] for r in delta}) == len(delta), 'Duplicate delta IDs')
    require(not set(ids).intersection(r[0] for r in delta), 'Occupied native ID')
    counts = Counter(key(r) for r in native)
    require(len({key(r) for r in delta}) == len(delta), 'Duplicate delta tuple')
    require(not set(counts).intersection(key(r) for r in delta), 'Occupied native tuple')
    # Preserve any pre-existing duplicates (reported); never introduce one.
    block = bytearray(strings)
    offsets = {'': 0}
    added = []
    for row in delta:
        refs = []
        for name in row[4:7]:
            if name not in offsets:
                offsets[name] = len(block)
                block.extend(name.encode('utf-8') + b'\0')
            refs.append(offsets[name])
        added.append((*row[:4], *refs, *row[7:]))
    final = sorted([*native, *added], key=key)
    raw = (struct.pack('<4s4I', b'WDBC', len(final), 10, 40, len(block))
           + b''.join(struct.pack('<10I', *r) for r in final) + block)
    reread, newstrings = read_dbc(raw)
    old = {r[0]: r for r in native}
    require(all(old[r[0]] == r for r in reread if r[0] in old), 'Baseline changed')
    require(newstrings.startswith(strings), 'Baseline strings changed')
    require([key(r) for r in reread] == sorted(key(r) for r in reread), 'Unsorted rows')
    require([decode(r, newstrings) for r in reread if r[0] not in old] == delta,
            'Delta round trip mismatch')
    return raw, [{'key': list(k), 'count': n} for k, n in sorted(counts.items()) if n > 1]


def validate_blp(raw):
    if raw[:4] == b'BLP2':
        require(len(raw) >= 148, 'Truncated BLP2 header')
        kind, encoding, alpha, alpha_encoding, has_mips, width, height = struct.unpack_from('<I4B2I', raw, 4)
        require(kind == 1 and encoding in (1, 2, 3) and alpha in (0, 1, 4, 8)
                and 0 < width <= 8192 and 0 < height <= 8192, 'Invalid BLP2 header')
        offsets = struct.unpack_from('<16I', raw, 20)
        sizes = struct.unpack_from('<16I', raw, 84)
        end, gap, mips = 1172 if encoding == 1 else 148, False, []
        require(len(raw) >= end, 'Truncated BLP2 palette')
        for i, (off, size) in enumerate(zip(offsets, sizes)):
            if not size:
                require(off == 0 or end <= off <= len(raw), 'Invalid empty BLP2 mip offset')
                gap = True
                continue
            require(not gap and off >= end and size > 0 and off + size <= len(raw),
                    f'Invalid BLP2 mip bounds/ordering: level={i} offset={off} size={size} previous_end={end} length={len(raw)} gap={gap}')
            w, h = max(1, width >> i), max(1, height >> i)
            if encoding == 1:
                expected = w * h + (w * h * alpha + 7) // 8
            elif encoding == 2:
                require(alpha_encoding in (0, 1, 7), 'Unsupported BLP2 DXT encoding')
                expected = ((w + 3) // 4) * ((h + 3) // 4) * (8 if alpha_encoding == 0 else 16)
            else:
                expected = w * h * 4
            require(size >= expected, 'Truncated BLP2 mip')
            mips.append(dict(level=i, offset=off, bytes=size, width=w, height=h))
            end = off + size
        require(bool(mips), 'BLP2 has no mip data')
        return dict(magic='BLP2', encoding=encoding, alpha_bits=alpha,
                    alpha_encoding=alpha_encoding, has_mips=has_mips,
                    width=width, height=height, mips=mips)
    require(len(raw) >= 156 and raw[:4] == b'BLP1', 'Expected BLP1/BLP2 texture')
    compression, flags, width, height, picture, subtype = struct.unpack_from('<6I', raw, 4)
    require(compression in (0, 1) and 0 < width <= 8192 and 0 < height <= 8192,
            'Invalid BLP1 dimensions/compression')
    offsets = struct.unpack_from('<16I', raw, 28)
    sizes = struct.unpack_from('<16I', raw, 92)
    header_end = 156
    if compression == 1:
        header_end += 1024
    else:
        require(len(raw) >= 160, 'Truncated JPEG BLP1')
        header_end = 160 + struct.unpack_from('<I', raw, 156)[0]
    require(len(raw) >= header_end, 'Truncated BLP1 palette/JPEG header')
    mips, end, gap = [], header_end, False
    for i, (off, size) in enumerate(zip(offsets, sizes)):
        if not size:
            require(off == 0 or end <= off <= len(raw), 'Invalid empty BLP1 mip offset')
            gap = True
            continue
        require(not gap and off >= end and size > 0 and off + size <= len(raw),
                'Invalid BLP1 mip bounds/ordering')
        w, h = max(1, width >> i), max(1, height >> i)
        if compression == 1:
            require(flags in (0, 1, 4, 8), 'Unsupported BLP1 alpha depth')
            require(size >= w * h + (w * h * flags + 7) // 8, 'Truncated palette mip')
        mips.append({'level': i, 'offset': off, 'bytes': size, 'width': w, 'height': h})
        end = off + size
    require(bool(mips), 'BLP1 has no mip data')
    return dict(magic='BLP1', compression=compression, alpha_bits=flags,
                width=width, height=height, picture_type=picture, subtype=subtype, mips=mips)


def sql_value(v):
    # Hex string literals work with or without NO_BACKSLASH_ESCAPES; comparison
    # casts to binary below to reject case differences and trailing spaces too.
    return ("CONVERT(X'" + v.encode().hex() + "' USING utf8mb4)") if isinstance(v, str) else str(v)


def render_sql(delta, rollback=False):
    routine = 'azerothcore_setup_forest_troll_skins' + ('_rollback' if rollback else '')
    tmp = 'forest_troll_skins_expected'
    engines = "= 'InnoDB'" if rollback else "IN ('InnoDB', 'MyISAM')"
    engine_error = 'target must be InnoDB' if rollback else 'target must be InnoDB or MyISAM'
    schema_note = ('-- Requires InnoDB charsections_dbc and routine privileges; execute without --force.\n'
                   '-- Rollback keeps the InnoDB structural migration; it never converts the engine back.'
                   if rollback else
                   '-- Requires routine privileges and ALTER privilege for a MyISAM baseline; execute without --force.\n'
                   '-- MyISAM converts once to InnoDB BEFORE the row transaction. ALTER TABLE implicitly\n'
                   '-- commits and is NOT transactional; the structural migration persists after rollback.')
    migration = ('' if rollback else '''  IF EXISTS (SELECT 1 FROM information_schema.TABLES
             WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'charsections_dbc'
             AND ENGINE = 'MyISAM') THEN
    -- Nontransactional DDL: implicit commit; deliberately retained on later failure/rollback.
    ALTER TABLE `charsections_dbc` ENGINE=InnoDB;
  END IF;
''')
    columns = ', '.join('`' + c + '`' for c in COLS)
    exact = ' AND '.join((f'BINARY a.`{c}` <=> BINARY e.`{c}`' if c.startswith('Texture')
                          else f'a.`{c}` <=> e.`{c}`') for c in COLS)
    same_tuple = ' AND '.join(f'a.`{c}` = e.`{c}`'
                              for c in ('Race', 'Gender', 'GenType', 'Type', 'Color'))
    values = ',\n'.join('  (' + ', '.join(sql_value(v) for v in r) + ')' for r in delta)
    action = (f'DELETE a FROM `charsections_dbc` a JOIN `{tmp}` e ON a.`Id` = e.`Id`;'
              if rollback else
              f'INSERT INTO `charsections_dbc` ({columns})\n'
              f'  SELECT {", ".join("e.`" + c + "`" for c in COLS)} FROM `{tmp}` e\n'
              '  LEFT JOIN `charsections_dbc` a ON a.`Id` = e.`Id` WHERE a.`Id` IS NULL;')
    return f'''-- Generated by tools/build_forest_troll_skins.py; setup artifact only.
-- {'Explicit rollback, intentionally outside custom manifest tree.' if rollback else 'Native race8 ForestTroll additive overlay: IDs20000..20089, colors18..23.'}
{schema_note}
-- Failure rolls back rows; inspect then DROP PROCEDURE `{routine}` and
-- DROP TEMPORARY TABLE `{tmp}` in that session before retrying.
USE `acore_world`;
DELIMITER $$
CREATE PROCEDURE `{routine}`()
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
  IF NOT EXISTS (SELECT 1 FROM information_schema.TABLES
                 WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'charsections_dbc'
                 AND ENGINE {engines}) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ForestTroll: {engine_error}';
  END IF;
  CREATE TEMPORARY TABLE `{tmp}` (
    `Id` INT UNSIGNED PRIMARY KEY, `Race` INT UNSIGNED, `Gender` INT UNSIGNED,
    `GenType` INT UNSIGNED, `TexturePath1` VARCHAR(255),
    `TexturePath2` VARCHAR(255), `TexturePath3` VARCHAR(255),
    `Flags` INT UNSIGNED, `Type` INT UNSIGNED, `Color` INT UNSIGNED,
    UNIQUE (`Race`, `Gender`, `GenType`, `Type`, `Color`)
  ) ENGINE=InnoDB;
  INSERT INTO `{tmp}` ({columns}) VALUES
{values};
{migration}  SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
  START TRANSACTION;
  IF EXISTS (SELECT 1 FROM `charsections_dbc` a JOIN `{tmp}` e
             ON a.`Id` = e.`Id` WHERE NOT ({exact})) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ForestTroll: owned ID has different fields';
  END IF;
  IF EXISTS (SELECT 1 FROM `charsections_dbc` a JOIN `{tmp}` e
             ON {same_tuple} WHERE a.`Id` <> e.`Id`) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ForestTroll: semantic tuple occupied';
  END IF;
  {action}
  COMMIT;
  DROP TEMPORARY TABLE `{tmp}`;
END$$
DELIMITER ;
CALL `{routine}`();
DROP PROCEDURE `{routine}`;
'''


def command(*args):
    return subprocess.run([str(MPQ), *map(str, args)], check=True,
                          capture_output=True, text=True).stdout


def extract(archive, member, dest):
    command('extract-one', archive, member, dest)
    return dest.read_bytes()


def build(output, turtle=Path('/home/dev/wow-turtle'), native=Path('/home/dev/wow-335')):
    manifest = json.loads(MANIFEST.read_text())
    require(not output.exists(), 'Output must be a fresh directory')
    # Refuse output inside either read-only reference client, including symlinks.
    output = output.resolve()
    require(not any(output.is_relative_to(p.resolve()) for p in (turtle, native)),
            'Output overlaps a reference client')
    roots = {'turtle': turtle, '335': native}
    archives, provenance = {}, {}
    for name, spec in manifest['archives'].items():
        path = roots[spec['client']] / spec['path']
        actual = sha(path)
        require(actual == spec['sha256'], f'Archive hash mismatch: {path}')
        archives[name] = path
        provenance[name] = dict(spec, bytes=path.stat().st_size)
    output.mkdir(parents=True)
    (output / 'Data').mkdir()
    with tempfile.TemporaryDirectory(prefix='forest-troll-') as temp:
        stage = Path(temp)
        source_raw = extract(archives['turtle_sections'], manifest['sections']['member'], stage / 'source')
        native_raw = extract(archives['native_sections'], manifest['sections']['member'], stage / 'native')
        for kind, raw in (('turtle', source_raw), ('native', native_raw)):
            require(digest(raw) == manifest['sections'][kind + '_sha256'], 'DBC hash mismatch: ' + kind)
        source_rows, source_strings = read_dbc(source_raw)
        native_rows, native_strings = read_dbc(native_raw)
        require(len(source_rows) == 6617 and len(native_rows) == 8958, 'Unexpected baseline row counts')
        selected = select_source(source_rows, source_strings)
        delta = make_delta(selected, manifest)
        require(max(r[0] for r in native_rows) < 20000, 'Native ID allocation boundary changed')
        namespace = manifest['target']['namespace']
        require(not any(text(native_strings, r[i]).lower().startswith(namespace.lower() + '\\')
                        for r in native_rows for i in (4, 5, 6)), 'Namespace already referenced')
        merged, duplicates = merge(native_rows, native_strings, delta)
        payload = {manifest['sections']['member']: merged}
        resources = []
        names = sorted({t for r in selected for t in r[4:7] if t})
        for i, name in enumerate(names):
            archive_key = 'male_textures' if '\\Male\\' in name else 'female_textures'
            raw = extract(archives[archive_key], name, stage / 'texture')
            info = validate_blp(raw)
            target = relocated(name, namespace)
            payload[target] = raw
            resources.append(dict(source_archive=archive_key, source_member=name,
                                  member=target, bytes=len(raw), sha256=digest(raw), **info))
        require(len(resources) == 162 and len(payload) == 163, 'Unexpected texture inventory')
        # SFileAddFileEx stores source mtimes; normalize before each create.
        entries = []
        for i, (name, raw) in enumerate(sorted(payload.items())):
            path = stage / f'member-{i}'
            path.write_bytes(raw)
            os.utime(path, (0, 0))
            entries.append(f'{path}|{name}')
        listing = stage / 'create.txt'
        listing.write_text('\n'.join(entries) + '\n')
        patch = output / 'Data/patch-S.MPQ'
        command('create', patch, listing)
        members = {}
        for line in command('list', patch).splitlines():
            name, size = line.rsplit('\t', 1)
            require(name not in members, 'Duplicate MPQ member')
            members[name] = int(size)
        require(set(members) == set(payload) | {'(listfile)'}, 'Unexpected/missing MPQ members')
        for name, raw in payload.items():
            require(members[name] == len(raw), 'MPQ member size mismatch')
            require(extract(patch, name, stage / 'roundtrip') == raw, 'MPQ member round trip mismatch')
        # Build twice with a real time separation in integration tests too;
        # this in-build repeat catches nondeterministic archive metadata.
        repeat = stage / 'repeat.MPQ'
        command('create', repeat, listing)
        require(sha(patch) == sha(repeat), 'MPQ is not byte deterministic')
        sql = render_sql(delta)
        rollback = render_sql(delta, rollback=True)
        delta_raw, _ = merge([], b'\0', delta)
        (output / 'CharSections.delta.dbc').write_bytes(delta_raw)
        (output / 'turtle_forest_troll_skins.sql').write_text(sql)
        (output / 'rollback.sql').write_text(rollback)
        report = dict(
            feature=manifest['feature'], manifest_sha256=sha(MANIFEST),
            inputs=provenance, sections=manifest['sections'],
            decisions=manifest['decisions'],
            counts=dict(native_rows=8958, source_rows=6617, added_rows=90,
                        male_rows=42, female_rows=48, final_rows=9048, textures=162,
                        payload_members=163, mpq_members_including_listfile=len(members)),
            preservation=dict(original_record_bytes=True, original_string_prefix=True,
                              final_physical_order='Race,Sex,Base,Variation,Color',
                              baseline_duplicate_tuples=duplicates, new_tuple_collisions=0,
                              original_string_bytes=len(native_strings)),
            validations=dict(blp_headers_and_mip_bounds=True, textures_byte_exact=True,
                             all_payload_members_roundtrip=True, two_mpq_creates_identical=True,
                             runtime_db_checked=False, runtime_or_visual_acceptance=False),
            patch_sha256=sha(patch), charsections_sha256=digest(merged),
            delta_dbc_sha256=digest(delta_raw),
            sql_sha256=digest(sql.encode()), rollback_sha256=digest(rollback.encode()),
            mpq_tool_sha256=sha(MPQ), mpq_members=members,
            source_to_target=[dict(source_id=s[0], target_id=d[0], race=d[1], sex=d[2],
                                   base=d[3], variation=d[8], source_color=s[9],
                                   color=d[9], flags=d[7], textures=list(d[4:7]))
                              for s, d in zip(selected, delta)], resources=resources)
        (output / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        sums = ('Data/patch-S.MPQ', 'report.json', 'CharSections.delta.dbc',
                'turtle_forest_troll_skins.sql', 'rollback.sql')
        (output / 'SHA256SUMS').write_text(''.join(f'{sha(output / n)}  {n}\n' for n in sums))
    return report


def publish(output):
    target = ROOT / 'client_patches/turtle_forest_troll'
    paths = {'Data/patch-S.MPQ': target / 'Data/patch-S.MPQ',
             'report.json': target / 'report.json',
             'turtle_forest_troll_skins.sql': ROOT / 'data/sql/custom/db_world/turtle_forest_troll_skins.sql',
             'rollback.sql': ROOT / 'data/sql/rollback/turtle_forest_troll_skins.sql'}
    for source, dest in paths.items():
        require(not dest.exists() or dest.read_bytes() == (output / source).read_bytes(),
                'Refusing to overwrite differing published file: ' + str(dest))
    for source, dest in paths.items():
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copyfile(output / source, dest)
    (target / 'SHA256SUMS').write_text(''.join(f'{sha(target / n)}  {n}\n'
                                            for n in ('Data/patch-S.MPQ', 'report.json')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'work/forest-troll-skins-r1')
    parser.add_argument('--turtle-client', type=Path, default=Path('/home/dev/wow-turtle'))
    parser.add_argument('--native-client', type=Path, default=Path('/home/dev/wow-335'))
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    report = build(args.output, args.turtle_client, args.native_client)
    if args.publish:
        publish(args.output)
    print(json.dumps(dict(output=str(args.output), counts=report['counts'],
                          patch_sha256=report['patch_sha256']), indent=2))


if __name__ == '__main__':
    main()
