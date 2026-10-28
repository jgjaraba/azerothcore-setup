#!/usr/bin/env python3
"""Durable regional source capture and deterministic consolidated-client hook.

Capture is an explicit one-time import; normal builds only consume source-lock.json.
No source builders, snapshots, runtime, or work directories are used by the hook.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'client_patches/archive/source-inputs/high-elf-map'
SOURCE_LOCK_SHA256 = '382394976410b1dbd1b23221f275da6ecc29a86df726c4cf02fc2410237607c0'
TAG = 'high-elf-map:'
T = 'regular_client/Data/patch-T.MPQ'
Z = 'regular_client/Data/patch-Z.mpq'
SCHEMAS = {'AreaTable': (36, list(range(11, 27))),
           'WMOAreaTable': (28, list(range(11, 27))),
           'WorldMapArea': (11, [3]), 'WorldMapOverlay': (17, [8])}


def merge(table, base, delta):
    """Append relocatable rows, retaining the original record/string byte prefixes."""
    import consolidate_client_patches as c
    fields, columns = SCHEMAS[table]
    bf, old, strings = c.parse_dbc(base)
    df, additions, ds = c.parse_dbc(delta)
    c.require(bf == df == fields, 'Regional DBC schema changed: ' + table)
    c.require(len({r[0] for r in old}) == len(old) and
              len({r[0] for r in additions}) == len(additions), 'Duplicate regional DBC IDs')
    sb, result = bytearray(strings), [list(r) for r in old]
    for row in additions:
        semantic = c.semantic_row(row, ds, columns)
        for other in result:
            if other[0] == row[0]:
                c.require(c.semantic_row(other, bytes(sb), columns) == semantic,
                          f'{table} ID collision: {row[0]}')
                continue
            if table == 'AreaTable':
                c.require(other[3] != row[3], 'AreaTable exploration-bit collision')
            elif table == 'WMOAreaTable':
                c.require(other[1:4] != row[1:4], 'WMOAreaTable natural-key collision')
            elif table == 'WorldMapArea':
                c.require(other[1:3] != row[1:3] and
                          c.string_at(bytes(sb), other[3]) != c.string_at(ds, row[3]),
                          'WorldMapArea natural-key collision')
            elif other[1] == row[1]:
                c.require(other[2:6] != row[2:6] and
                          c.string_at(bytes(sb), other[8]) != c.string_at(ds, row[8]),
                          'WorldMapOverlay natural-key collision')
        if any(r[0] == row[0] for r in result):
            continue
        new = list(row)
        for col in columns:
            text = c.string_at(ds, row[col])
            # Overlay builder deliberately appends even empty strings.
            new[col] = len(sb) if text or table == 'WorldMapOverlay' else 0
            if text or table == 'WorldMapOverlay':
                sb.extend(text + b'\0')
        result.append(new)
    if len(result) == len(old):
        return base
    return c.encode(fields, result, sb)


def load():
    import consolidate_client_patches as c
    path = SOURCE / 'source-lock.json'
    c.require(c.file_sha(path) == SOURCE_LOCK_SHA256, 'High-elf source lock changed')
    lock = json.loads(path.read_text())
    c.require(c.file_sha(c.LOCK) == lock['native_source_lock_sha256'], 'Native source lock changed')
    actual = {str(p.relative_to(SOURCE)) for p in SOURCE.rglob('*') if p.is_file()}
    c.require(actual == set(lock['files']) | {'source-lock.json', 'README.md'},
              'High-elf source inventory changed')
    for relative, spec in lock['files'].items():
        c.require(c.norm(relative) == relative.lower(), 'Unsafe high-elf source path')
        path = SOURCE / relative
        c.require(not path.is_symlink() and path.resolve().is_relative_to(SOURCE.resolve()) and
                  path.stat().st_size == spec['size'] and c.file_sha(path) == spec['sha256'],
                  'High-elf source changed: ' + relative)
    return lock


def source_members(source):
    lock = load()
    relative = source.removeprefix(TAG)
    spec = lock['files'][relative]
    return {spec['member'].lower().replace('\\', '/'): (spec['member'], (SOURCE / relative).read_bytes())}


def integrate(native):
    import consolidate_client_patches as c
    lock = load()
    planned = {p: dict(entries) for p, entries in native.items()}
    for edit in lock['edits']:
        package, member = edit['package'], edit['member']
        key = c.norm(member)
        old = native[package].get(key)
        c.require((c.sha(old['data']) if old else None) == edit['previous_sha256'],
                  'High-elf pre-integration member changed: ' + package + ':' + member)
        if 'delta' in edit:
            base = (SOURCE / edit['baseline']).read_bytes()
            if old:
                c.require(base == old['data'], 'High-elf independent baseline differs from native plan')
            raw = merge(edit['table'], base, (SOURCE / edit['delta']).read_bytes())
            c.require(merge(edit['table'], raw, (SOURCE / edit['delta']).read_bytes()) == raw,
                      'Non-idempotent regional DBC')
        else:
            raw = (SOURCE / edit['source']).read_bytes()
        c.require(c.sha(raw) == edit['result_sha256'], 'High-elf reconstructed result differs')
        provenance = [TAG + edit['baseline'], TAG + edit['delta']] if 'delta' in edit else [TAG + edit['source']]
        planned[package][key] = {'name': member, 'data': raw, 'category': c.category(member)
                                 if 'delta' in edit else 'geography',
                                 'provenance': provenance}
    # Every old member outside the explicit edit set must remain byte-exact.
    touched = {(e['package'], c.norm(e['member'])) for e in lock['edits']}
    for package, entries in native.items():
        for key, entry in entries.items():
            c.require((package, key) in touched or planned[package][key] == entry,
                      'Unrelated client member changed: ' + key)
    return planned


def audit(native, planned):
    import consolidate_client_patches as c
    lock = load()
    c.require(c.inventory(integrate(native)) == c.inventory(planned), 'Regional plan drift')
    diffs = {}
    for edit in lock['edits']:
        if 'delta' not in edit:
            continue
        base = (SOURCE / edit['baseline']).read_bytes()
        result = planned[edit['package']][c.norm(edit['member'])]['data']
        diff = c.record_diff(base, result, edit['table'].lower())
        c.require(not diff['changed'] and not diff['removed'] and diff == edit['diff'],
                  'Regional DBC native records changed')
        fields, rows, strings = c.parse_dbc(base)
        _, merged, ms = c.parse_dbc(result)
        c.require(merged[:len(rows)] == rows and ms.startswith(strings), 'Native DBC bytes changed')
        diffs[edit['package'] + ':' + edit['member']] = diff
    from build_crypt_cartography import parse_trs
    key = 'textures/minimap/md5translate.trs'
    before = parse_trs(native[T][key]['data'])
    after = parse_trs(planned[T][key]['data'])
    allowed = set(lock['trs_changed_keys'])
    c.require(set(before) <= set(after) and all(after[k] == v for k, v in before.items() if k not in allowed),
              'Unowned TRS mappings changed')
    c.require(not any(k.endswith('.dbc') for k in planned[T]), 'Geography T contains DBC')
    for package, entries in planned.items():
        if not package.startswith('regular_client/'):
            continue
        for key in entries:
            if key.startswith('dbfilesclient/'):
                table = key.split('/')[-1][:-4]
                c.require((table not in c.LOCALIZED) if package == Z else
                          (package != T and package.endswith('-Z.MPQ') and table in c.LOCALIZED),
                          'Regional DBC ownership violation: ' + package + ':' + key)
    return {'source_lock_sha256': SOURCE_LOCK_SHA256, 'dbc_diffs': diffs,
            'previous_members_preserved_byteexact': sum(len(v) for v in native.values()) -
                sum(e['previous_sha256'] is not None for e in lock['edits']),
            'explicit_edits': len(lock['edits']), 'geographic_dbc_in_T': False,
            'native_records_and_strings_byteexact': True, 'unowned_trs_mappings_preserved': True,
            'client_render_and_gameplay': 'NOT RUN',
            'cartography_stage_limitations': lock['limitations'],
            'limitations_scope': 'Upstream cartography stage only; combined delivery also includes final ADT/assets. '
                'Offline resource closure is not in-game acceptance.'}


def capture(args):
    """Import final artifacts once, including independent baseline/result evidence."""
    import consolidate_client_patches as c
    c.require(not SOURCE.exists(), 'Durable regional source already exists; review an explicit migration')
    previous = None
    if args.baseline_source:
        # Explicit regional migration: reuse only the independently pinned old
        # bases, never replace the native build with already integrated tables.
        pin = args.baseline_source / 'source-lock.json'
        c.require(args.baseline_source_sha256 and c.file_sha(pin) == args.baseline_source_sha256,
                  'Previous regional source lock changed or explicit historical pin missing')
        previous = json.loads(pin.read_text())
    assets = json.loads((args.assets / 'manifest.json').read_text())
    cart = json.loads((args.cartography / 'manifest.json').read_text())
    terrain = json.loads((args.terrain / 'manifest.json').read_text())
    c.require(assets['asset_closure_complete'] and not assets['blockers'], 'Assets not closed')
    c.require(cart['closure_complete'] and not cart['missing'], 'Cartography not closed')
    c.require(terrain['terrain_ready'], 'Terrain not ready')
    from high_elf_map_dbc import validate_assets_wmo
    placed_wmo_validation = validate_assets_wmo(
        (args.cartography / 'files/deltas/WMOAreaTable.dbc').read_bytes(), args.assets)
    c.require(cart['placed_wmo_validation'] == placed_wmo_validation,
              'Cartography placed WMO validation differs from final assets')
    c.require(cart['inputs']['assets-manifest']['sha256'] == c.file_sha(args.assets / 'manifest.json'),
              'Cartography was not generated from the selected final assets')
    c.require(cart['inputs']['terrain-report']['sha256'] == c.file_sha(args.terrain / 'manifest.json'),
              'Cartography was not generated from the selected final terrain')
    for tile in assets['tiles']:
        original = args.terrain / Path(tile['source']['path']).name
        c.require(c.file_sha(original) == tile['source']['sha256'], 'Final terrain/assets provenance mismatch')
    native = c.plan(json.loads(c.LOCK.read_text()), c.Sources(json.loads(c.LOCK.read_text())), include_high_elf=False)
    # Capture never trusts an already modified published profile as the native base.
    c.validate_native_delivery(native, json.loads(c.LOCK.read_text()))
    SOURCE.mkdir(parents=True)
    lock = {'version': 1, 'files': {}, 'edits': [], 'limitations': cart['limitations'],
            'native_source_lock_sha256': c.file_sha(c.LOCK), 'trs_changed_keys': []}
    if previous:
        lock['previous_regional_source_lock_sha256'] = args.baseline_source_sha256

    def store(relative, raw, member=None):
        path = SOURCE / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        lock['files'][relative] = {'sha256': c.sha(raw), 'size': len(raw)}
        if member:
            lock['files'][relative]['member'] = member
        return relative

    def add(package, member, raw, source):
        member = member.replace('/', '\\')
        key = c.norm(member)
        c.require(not any(e['package'] == package and c.norm(e['member']) == key for e in lock['edits']),
                  'Duplicate geographic source member')
        old = native[package].get(key)
        edit = {'package': package, 'member': member, 'result_sha256': c.sha(raw),
                'previous_sha256': c.sha(old['data']) if old else None, 'source': source}
        lock['edits'].append(edit)
        return edit

    for label, directory in [('assets', args.assets), ('terrain', args.terrain), ('cartography', args.cartography)]:
        store('evidence/' + label + '-manifest.json', (directory / 'manifest.json').read_bytes())
    for f in assets['files']:
        member = f['path'].replace('\\', '/')
        raw = (args.assets / 'files' / member).read_bytes()
        c.require(c.sha(raw) == f['sha256'], 'Asset hash changed')
        c.require(not member.lower().endswith(('.dbc', '.wdt', '.wdl')), 'Unexpected geography payload')
        relative = store('shared/' + member, raw, member)
        add(T, member, raw, relative)
    for f in cart['files']:
        member = f['path'].replace('\\', '/')
        if member.startswith(('server/', 'enUS/', 'esES/', 'deltas/')):
            continue
        c.require(member.lower().startswith(('textures/minimap/', 'interface/worldmap/')),
                  'Unexpected cartography client payload: ' + member)
        raw = (args.cartography / 'files' / member).read_bytes()
        c.require(c.sha(raw) == f['sha256'], 'Cartography hash changed')
        add(T, member, raw, store('shared/' + member, raw, member))
    from build_crypt_cartography import parse_trs
    trs = 'textures/minimap/md5translate.trs'
    previous_trs = parse_trs(native[T][trs]['data'])
    edit = next(e for e in lock['edits'] if c.norm(e['member']) == trs)
    after = parse_trs((SOURCE / edit['source']).read_bytes())
    lock['trs_changed_keys'] = sorted(k for k in previous_trs if previous_trs[k] != after[k])
    for table in SCHEMAS:
        delta = (args.cartography / 'files/deltas' / (table + '.dbc')).read_bytes()
        member = 'DBFilesClient/' + table + '.dbc'
        dpath = store('deltas/' + table + '.dbc', delta, member)
        for locale in (('enUS', 'esES') if table in ('AreaTable', 'WMOAreaTable') else ('enUS',)):
            package = 'regular_client/Data/' + locale + '/patch-' + locale + '-Z.MPQ' if table in ('AreaTable', 'WMOAreaTable') else Z
            # Results were authored on independent pre-integration regular/stock bases.
            result = (args.cartography / 'files' / locale / 'DBFilesClient' / (table + '.dbc')).read_bytes()
            spec = cart['baselines'][locale][table]
            old = native[package].get(c.norm(member))
            if old:
                base = old['data']
            elif previous:
                entry = next(e for e in previous['edits'] if e['package'] == package and
                             c.norm(e['member']) == c.norm(member))
                base = (args.baseline_source / entry['baseline']).read_bytes()
                pinned = previous['files'][entry['baseline']]
                c.require(c.sha(base) == pinned['sha256'] and len(base) == pinned['size'],
                          'Previous independent baseline changed')
            else:
                # Recover exactly the independent base used by cartography, never a full profile table as delta.
                inp = cart['inputs'][locale + '/' + table]
                base = c.extract(Path(inp['archive']), member.replace('/', '\\'))
            # Cartography may have been rerun on an already integrated profile.
            # Accept that provenance only if it reproduces the same full result
            # from the untouched independent pre-map base staged here.
            c.require(spec['sha256'] in (c.sha(base), c.sha(result)),
                      'Independent/cartography baseline mismatch: ' + locale + '/' + table)
            _, base_rows, _ = c.parse_dbc(base)
            _, delta_rows, _ = c.parse_dbc(delta)
            c.require(not {r[0] for r in base_rows}.intersection(r[0] for r in delta_rows),
                      'Independent baseline already contains regional rows')
            merged = merge(table, base, delta)
            c.require(merged == result, 'Delta does not reproduce independent profile result: ' + table)
            e = add(package, member, result, '')
            del e['source']
            e.update(table=table, delta=dpath,
                     baseline=store('baselines/' + locale + '/' + table + '.dbc', base, member),
                     diff=c.record_diff(base, result, table.lower()))
            store('results/' + locale + '/' + table + '.dbc', result, member)
            if table in ('WorldMapArea', 'WorldMapOverlay'):
                other = (args.cartography / 'files/esES/DBFilesClient' / (table + '.dbc')).read_bytes()
                c.require(c.rows(other, table.lower()) == c.rows(result, table.lower()),
                          'Nonlocalized cartography differs between locales: ' + table)
    lock['edits'].sort(key=lambda e: (e['package'], c.norm(e['member'])))
    c.dump(SOURCE / 'source-lock.json', lock)
    (SOURCE / 'README.md').write_text(
        '# High Elf Map0 — durable regular-client source\n\n'
        'This directory is a build input, never an installation profile. '
        '`source-lock.json` pins every payload, independent baseline, delta, '
        'expected full result and upstream evidence manifest by SHA-256/size. '
        'Its own SHA-256 is pinned in `tools/package_high_elf_map.py`.\n\n'
        'The hook reconstructs the historical consolidation first, verifies all '
        'original regular delivery hashes without modifying the old source lock, '
        'then applies only the listed edits. Full DBCs are rebuilt from staged '
        'independent baselines plus relocatable deltas and compared against '
        'the pinned result hashes. Diffs are in each DBC edit. Native record '
        'and string-block prefixes remain byte-exact. `work/` paths in evidence '
        'are provenance only; the normal hook never opens them.\n\n'
        'Ownership: shared geography (including isolated Character/Custom/HighElfMap '
        'models) in T without DBC; AreaTable and WMOAreaTable in both locale Z; '
        'WorldMapArea and WorldMapOverlay in root Z. S and all unrelated members '
        'and HD remain byte-exact. The complete TRS retains crypt/native mappings '
        'outside its explicit regional update list.\n\n'
        'Build from repository root with TMPDIR="$PWD/work/tmp":\n\n'
        '```sh\n'
        'work/new-races-image-venv/bin/python tools/consolidate_client_patches.py '
        '--output work/high-elf-map-rebuild --reproducible\n'
        'work/new-races-image-venv/bin/python tools/consolidate_client_patches.py '
        '--verify client_patches\n'
        '```\n\n'
        'Export TMPDIR for both commands. To reconstruct the exact old delivery '
        'use `--native-only --output work/high-elf-map-rollback --reproducible`; '
        'verify it with `--native-only --verify work/high-elf-map-rollback`. '
        'Publication remains the consolidator transactional `--publish` operation. '
        'Manual installation/rollback is described in client_patches/README.md. '
        'No snapshots or server files are installed by this hook.\n\n'
        'An explicit source migration may use `--baseline-source DIRECTORY '
        '--baseline-source-sha256 HISTORICAL_LOCK_SHA256` during capture. '
        'This historical pin is separate from the current active-source pin. '
        'Only independently pinned baseline files are recovered; integrated '
        'result tables are never accepted as a new pre-map baseline.\n')
    print('SOURCE_LOCK_SHA256 =', c.file_sha(SOURCE / 'source-lock.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', action='store_true', required=True)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--terrain', type=Path, required=True)
    parser.add_argument('--cartography', type=Path, required=True)
    parser.add_argument('--baseline-source', type=Path,
                        help='Explicit migration: recover independently pinned pre-map baselines from previous source')
    parser.add_argument('--baseline-source-sha256',
                        help='Required with --baseline-source: explicit SHA-256 of that historical source lock')
    capture(parser.parse_args())
