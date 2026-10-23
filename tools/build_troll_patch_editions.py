#!/usr/bin/env python3
"""Build patch-S v3 primary and optional full replacement; never deploy clients/DB.

Default rebuilds pinned v2 from original read-only MPQs. --base-version current
uses only the exact pinned v2 publication (archive preferred). --publish verifies
all existing destinations before preserving v2 and replacing owned artifacts.
The optional patch replaces primary at the SAME filename; never load both.
"""
import argparse
import json
from pathlib import Path
import shutil
import struct
import tempfile

import build_troll_customizations as legacy
from build_troll_face_format_test import palette_encode
from crypt_release_client import members, key

ROOT = legacy.ROOT
MANIFEST = ROOT / 'tools/troll-patch-editions.json'
PACKAGE = Path('client_patches/turtle_forest_troll')
SECTIONS = r'DBFilesClient\CharSections.dbc'
PRODUCTS = ('Data/patch-S.MPQ', 'report.json', 'SHA256SUMS')
# Release identities are outside the recipe manifest to avoid a report/manifest
# checksum cycle. A self-consistent foreign report cannot bless new bytes.
OLD_PUBLICATIONS = {
    'primary': dict(zip(PRODUCTS, (
        '2bd2ce7adb7bf678f110b8be43d8e0fd5eb168c522e6857eff17f15c3d455ce8',
        '7a3c806ed49a303548f809c8b91f92f3b9e025058c18a81957b1624ca06361d0',
        'f7d93e7c341f6bebdd687f064addc94b0491685974922333e98389f1c455c2e2'))),
    'optional-extra-skins': dict(zip(PRODUCTS, (
        'a09f4f6c69957dc770c7bc458772eda3ee641f675925fdb4a5c7045026731769',
        'd9cb2d9f5c9e8ef7bc83c82207885c5c72a278665c92729b4bd0b2d99e8dcb62',
        'f254538481cc73768ac184ae04c0be5c9629474a686bb98e7cde28c623d2cba6'))),
}
PUBLICATIONS = {
    'primary': dict(zip(PRODUCTS, (
        '2bd2ce7adb7bf678f110b8be43d8e0fd5eb168c522e6857eff17f15c3d455ce8',
        '5c4b59366295007440a58e2d8e081719f40715700b9e0a721fd57191074aeb9c',
        '5f04fb1b3ccc6d13830ed84e6d7e50874f2d485eb11dc7baa3e1efe283d0c5f8'))),
    'optional-extra-skins': dict(zip(PRODUCTS, (
        '2890f2b54fc99edfae948d8dceccb21edbfee26fd8089ec7f2a5a370b2dda6e4',
        '9a4c37da5f5bccfe71ecb190f7888f79f43b48df3bb538d88494dc4cc06e9752',
        '44e691fb562c0b54e9fdd7d247e62f62ce0896630ffba4fdcbe3c94d0b71190f'))),
}
SQL_PATHS = {
    'primary.sql': 'data/sql/custom/db_world/turtle_troll_customizations.sql',
    'primary-rollback.sql': 'data/sql/rollback/turtle_troll_customizations.sql',
    'optional.sql': 'data/sql/optional/db_world/turtle_troll_extra_skins.sql',
    'optional-rollback.sql': 'data/sql/rollback/turtle_troll_extra_skins.sql',
    'legacy.sql': 'data/sql/history/troll-v2-full/apply.sql',
    'legacy-rollback.sql': 'data/sql/history/troll-v2-full/rollback.sql',
}
require, sha, digest = legacy.require, legacy.sha, legacy.digest


def manifest():
    return json.loads(MANIFEST.read_text())


def verify_base(path):
    return legacy.verify_publication(path, manifest()['base'])


def base_path(root=ROOT):
    package = root / PACKAGE
    return package / 'v2' if (package / 'v2').exists() else package


def split_rows(report):
    primary = [r for r in report['sql_rows'] if r[3] in (2, 3)]
    optional = [r for r in report['sql_rows'] if r[3] in (0, 1, 4)]
    forest = [[r['target_id'], r['race'], r['sex'], r['base'], *r['textures'],
               r['flags'], r['variation'], r['color']] for r in report['source_to_target']]
    require((len(primary), len(optional), len(forest)) == (208, 156, 90), 'Unexpected row partition')
    return primary, optional, forest


def retired_row(row):
    return row[1] == 8 and row[2] == 0 and row[3] in (0, 1, 4) and row[9] in (33, 34, 35)


def optional_sql(active, retired, prerequisites=(), rollback=False):
    # One expected156 table guards BOTH current135 and legacy21 before any DML.
    # This also rejects foreign semantic tuples at retired colors.
    sql = render_sql(active + retired, 'optional', rollback, prerequisites=prerequisites)
    sql = '-- Current optional135 + exact legacy cleanup21 (male colors33..35).\n' + sql
    if not rollback:
        ids = ','.join(str(r[0]) for r in retired)
        action = '  INSERT INTO `charsections_dbc`'
        sql = sql.replace(action, f'  DELETE a FROM `charsections_dbc` a JOIN `troll_extra_skins_expected` e ON a.`Id` = e.`Id` WHERE e.`Id` IN ({ids});\n' + action)
        sql = sql.replace('WHERE a.`Id` IS NULL;', f'WHERE a.`Id` IS NULL AND e.`Id` NOT IN ({ids});')
    return sql


def render_sql(rows, edition, rollback=False, prerequisites=(), dependents=()):
    sql = legacy.render_sql(rows, rollback)
    namespace = 'troll_primary' if edition == 'primary' else 'troll_extra_skins'
    sql = sql.replace('troll_customizations', namespace)
    sql = sql.replace('tools/build_troll_customizations.py', 'tools/build_troll_patch_editions.py')
    sql = sql.replace('Troll extension:247 new IDs20100..20346 +117 exact native hair overrides; preserves Forest90.',
                      f'Patch-S v3 {edition}: {len(rows)} exact overlays; independently applied/removed.')
    tmp = namespace + '_prerequisites'
    guard = ''
    if prerequisites:
        columns = ', '.join('`' + c + '`' for c in legacy.forest.COLS)
        exact = ' AND '.join((f'CAST(a.`{c}` AS BINARY) <=> CAST(e.`{c}` AS BINARY)'
                             if c.startswith('Texture') else f'a.`{c}` <=> e.`{c}`')
                            for c in legacy.forest.COLS)
        values = ',\n'.join('(' + ', '.join(legacy.forest.sql_value(v) for v in r) + ')'
                             for r in prerequisites)
        guard = f'''  CREATE TEMPORARY TABLE `{tmp}` LIKE `{namespace}_expected`;
  INSERT INTO `{tmp}` ({columns}) VALUES {values};
  IF EXISTS (SELECT 1 FROM `{tmp}` e LEFT JOIN `charsections_dbc` a ON a.`Id` = e.`Id`
             WHERE a.`Id` IS NULL OR NOT ({exact})) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Optional skins require exact Forest90 and primary208';
  END IF;
  DROP TEMPORARY TABLE `{tmp}`;
'''
        sql = sql.replace('-- Failure rolls back rows;', f'-- On failure also inspect/drop temporary `{tmp}`.\n-- Failure rolls back rows;')
    if dependents:
        ids = ','.join(str(r[0]) for r in dependents)
        guard += f'''  IF EXISTS (SELECT 1 FROM `charsections_dbc` WHERE `Id` IN ({ids})) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Remove optional skins before primary rollback';
  END IF;
'''
    return sql.replace('  START TRANSACTION;\n', '  START TRANSACTION;\n' + guard)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def checksum(directory):
    (directory / 'SHA256SUMS').write_text(''.join(f'{sha(directory / n)}  {n}\n'
                                                for n in PRODUCTS[:2]))


def build(output, base_version='sources'):
    output = Path(output).resolve()
    require(not output.exists(), 'Output must be fresh')
    require(not any(output.is_relative_to(p.resolve()) for p in
                    (ROOT / PACKAGE, Path('/home/dev/wow-335'), Path('/home/dev/wow-turtle'))),
            'Output overlaps publication or reference clients')
    require(base_version in ('sources', 'current'), 'Unknown base version')
    m = manifest()
    require(m['removed_male_colors'] == [33, 34, 35] and not m['quantization_allowlist'], 'Unexpected removal recipe')
    with tempfile.TemporaryDirectory(prefix='troll-editions-') as temp:
        stage = Path(temp)
        if base_version == 'sources':
            base = stage / 'v2-source'
            report = legacy.build(base)
            # Historical scratch contains extra checksum entries; pin its actual
            # MPQ/report, then compare its two-file publication checksum recipe.
            for n in PRODUCTS[:2]:
                require(sha(base / n) == m['base'][n], 'Reconstructed v2 mismatch: ' + n)
            expected = ''.join(f'{sha(base / n)}  {n}\n' for n in PRODUCTS[:2])
            require(digest(expected.encode()) == m['base']['SHA256SUMS'], 'Reconstructed v2 checksum mismatch')
        else:
            base = base_path()
            report = verify_base(base)
        original = {n: raw for n, raw in members(legacy.forest.MPQ, base / PRODUCTS[0]).values()}
        primary_rows, all_skin_rows, forest_rows = split_rows(report)
        retired = [r for r in all_skin_rows if retired_row(r)]
        skin_rows = [r for r in all_skin_rows if not retired_row(r)]
        removed = {name for r in all_skin_rows for name in r[4:7] if name}
        active_refs = {name for r in skin_rows + primary_rows + forest_rows for name in r[4:7] if name}
        retired_members = {name for r in retired for name in r[4:7] if name} - active_refs
        faces = sorted({name for r in skin_rows if r[3] == 1 for name in r[4:6]})
        require((len(retired), len(skin_rows), len(retired_members)) == (21, 135, 12), 'Unexpected retirement')
        require(len(removed) == 93 and len(faces) == 36 and len(original) == 306, 'Unexpected texture inventory')
        optional = {n: raw for n, raw in original.items() if n not in retired_members}
        changes = []
        for name in faces:
            before = original[name]
            after, metrics = palette_encode(before, allow_quantize=False)
            quantized = not metrics['top_rgba_exact']
            require(not quantized, 'Remaining face must be lossless')
            top = metrics['mip_errors'][0]
            top['rgb_p99'] = 0.0
            optional[name] = after
            changes.append(dict(member=name, before_sha256=digest(before), after_sha256=digest(after),
                                quantized=quantized, **metrics))
        # Preserve the accepted A/B pair serialization, independently of its report.
        trial = ROOT / PACKAGE / 'face-format-test/Data/patch-S.MPQ'
        require(sha(trial) == m['accepted_trial_sha256'], 'Accepted A/B changed')
        trial_members = members(legacy.forest.MPQ, trial)
        for part in ('Lower', 'Upper'):
            name = rf'Character\Custom\TurtleTroll\Male\100_Face{part}.blp'
            require(optional[name] == trial_members[key(name)][1], 'Accepted A/B face bytes changed')
        primary = {n: raw for n, raw in original.items() if n not in removed}
        rows, strings = legacy.forest.read_dbc(original[SECTIONS])
        ids = {r[0] for r in all_skin_rows}
        retained = [r for r in rows if r[0] not in ids]
        require(len(retained) == 9139 and len(rows) == 9295, 'Unexpected DBC partition')
        # Keep every retained raw record and the COMPLETE original string block.
        primary[SECTIONS] = (struct.pack('<4s4I', b'WDBC', len(retained), 10, 40, len(strings))
                             + b''.join(struct.pack('<10I', *r) for r in retained) + strings)
        optional_rows = [r for r in rows if r[0] not in {r[0] for r in retired}]
        optional[SECTIONS] = (struct.pack('<4s4I', b'WDBC', len(optional_rows), 10, 40, len(strings))
                             + b''.join(struct.pack('<10I', *r) for r in optional_rows) + strings)
        old_path = ROOT / PACKAGE / 'optional-extra-skins'
        comparison = m['previous_optional_comparison']
        remaining_hashes = {n: digest(raw) for n, raw in sorted(optional.items()) if n != SECTIONS}
        fingerprint = digest(json.dumps(remaining_hashes, sort_keys=True, separators=(',', ':')).encode())
        require(fingerprint == comparison['remaining_member_hashes_sha256'], 'Remaining optional differs from pinned old payload')
        require(comparison['patch_sha256'] == OLD_PUBLICATIONS['optional-extra-skins'][PRODUCTS[0]] and
                set(comparison['removed_member_sha256']) == retired_members,
                'Old optional proof identity differs')
        if old_path.exists() and sha(old_path / PRODUCTS[0]) == OLD_PUBLICATIONS['optional-extra-skins'][PRODUCTS[0]]:
            legacy.verify_publication(old_path, OLD_PUBLICATIONS['optional-extra-skins'])
            old_payload = {n: raw for n, raw in members(legacy.forest.MPQ, old_path / PRODUCTS[0]).values()}
            require(set(optional) == set(old_payload) - retired_members, 'Old optional inventory differs')
            require(all(raw == old_payload[n] for n, raw in optional.items() if n != SECTIONS), 'Remaining optional bytes changed')
            old_rows, old_strings = legacy.forest.read_dbc(old_payload[SECTIONS])
            require(old_strings == strings and optional_rows == [r for r in old_rows if r[0] not in {r[0] for r in retired}], 'Old optional records changed')
            require(comparison['removed_member_sha256'] == {n: digest(old_payload[n]) for n in sorted(retired_members)},
                    'Old optional removed hashes differ')
        output.mkdir(parents=True)
        sql = {
            'primary.sql': render_sql(primary_rows, 'primary'),
            'primary-rollback.sql': render_sql(primary_rows, 'primary', True, dependents=all_skin_rows),
            'optional.sql': optional_sql(skin_rows, retired, prerequisites=forest_rows + primary_rows),
            'optional-rollback.sql': optional_sql(skin_rows, retired, rollback=True),
            'legacy.sql': legacy.render_sql(report['sql_rows']),
            'legacy-rollback.sql': legacy.render_sql(report['sql_rows'], True),
        }
        for name, text in sql.items():
            (output / name).write_text(text)
        editions = {}
        for edition, payload, selected in (('primary', primary, primary_rows), ('optional-extra-skins', optional, skin_rows)):
            directory = output / edition
            (directory / 'Data').mkdir(parents=True)
            patch = directory / PRODUCTS[0]
            legacy.create_mpq(patch, payload, stage)
            repeat = stage / (edition + '-repeat.MPQ')
            legacy.create_mpq(repeat, payload, stage)
            require(sha(patch) == sha(repeat), 'Non-deterministic edition')
            resources = []
            for resource in report['resources']:
                name = resource['member']
                if name in payload:
                    raw = payload[name]
                    legacy.forest.validate_blp(raw)
                    resources.append(dict(resource, sha256=digest(raw), bytes=len(raw),
                                          v2_sha256=digest(original[name]), v2_byte_exact=raw == original[name],
                                          **legacy.forest.validate_blp(raw)))
            result = dict(kind='troll-patch-edition', version=3,
                          edition='primary' if edition == 'primary' else 'optional',
                          base_pins=m['base'], recipe='tools/build_troll_customizations.py',
                          manifest_sha256=sha(MANIFEST), source_inputs=report['inputs'],
                          source_provenance=report['provenance'], source_to_target=report['source_to_target'],
                          sql_rows=selected, primary_sql_rows=primary_rows, optional_sql_rows=skin_rows,
                          hair_changes=report['hair_changes'], natural_style_rows=report['natural_style_rows'],
                          resources=resources, face_conversions=changes if edition != 'primary' else [],
                           removal=dict(colors=[33, 34, 35], sex='male', rows=retired,
                                        ids=[r[0] for r in retired], members={n: digest(original[n]) for n in sorted(retired_members)},
                                        previous_optional_comparison=comparison),
                           counts=dict(final_rows=len(retained) if edition == 'primary' else len(optional_rows),
                                      textures=len(resources), payload_members=len(payload), sql_rows=len(selected),
                                       primary_sql_rows=208, optional_sql_rows=135, legacy_cleanup_rows=21, accepted_rows=90,
                                      hair_modified_rows=117, new_facial_rows=91, natural_style_final_rows=229,
                                       converted_faces=0 if edition == 'primary' else 36,
                                      lossless_top_faces=0 if edition == 'primary' else 36,
                                       quantized_top_faces=0),
                          patch_sha256=sha(patch), charsections_sha256=digest(payload[SECTIONS]),
                          natural_styles_sha256=report['natural_styles_sha256'],
                          mpq_members={n: len(raw) for n, raw in sorted(payload.items())},
                          sql_artifacts={n: digest(text.encode()) for n, text in sql.items()},
                          contract=dict(filename='Data/patch-S.MPQ', full_replacement=True,
                                        never_load_both_editions=True, primary_rollback_requires_no_optional=True),
                          validations=dict(two_mpq_creates_identical=True, all_members_roundtrip=True,
                                           retained_v2_bytes_exact=True, all_mip_alpha_exact=True,
                                           accepted_trial_pair_byte_exact=True,
                                           client_test_run=False, live_database_changed=False))
            write_json(directory / 'report.json', result)
            checksum(directory)
            editions[edition] = result
        return editions


def publish(output, root=None):
    root = Path(root or ROOT)
    output = Path(output)
    package = root / PACKAGE
    pins = manifest()['base']
    base = base_path(root)
    base_report = verify_base(base)
    replacements = {}
    for edition, target in (('primary', package), ('optional-extra-skins', package / 'optional-extra-skins')):
        source = output / edition
        report = legacy.verify_publication(source, PUBLICATIONS[edition])
        require(report['kind'] == 'troll-patch-edition' and report['version'] == 3 and
                report['edition'] == ('primary' if edition == 'primary' else 'optional') and
                report['manifest_sha256'] == sha(MANIFEST) and
                report['base_pins'] == pins, 'Unknown edition recipe')
        for name, expected in report['sql_artifacts'].items():
            require(sha(output / name) == expected, 'Output SQL hash mismatch: ' + name)
        if target.exists() and (target / 'report.json').exists():
            legacy.verify_publication(target)
            known_v2 = all(sha(target / n) == pins[n] for n in PRODUCTS)
            same = all((target / n).read_bytes() == (source / n).read_bytes() for n in PRODUCTS)
            known_old = all(sha(target / n) == OLD_PUBLICATIONS[edition][n] for n in PRODUCTS)
            require(same or known_old or (edition == 'primary' and known_v2), 'Refusing unknown current edition')
        elif target.exists():
            require(not any(target.iterdir()), 'Refusing partial edition')
        for name in PRODUCTS:
            replacements[target / name] = source / name
    # Archive exact pinned v2 before replacing it. Preflight archive too.
    archive = package / 'v2'
    if archive.exists():
        verify_base(archive)
    else:
        for name in PRODUCTS:
            replacements[archive / name] = base / name
    for name, relative in SQL_PATHS.items():
        dest = root / relative
        if dest.exists():
            known = [(output / name).read_bytes()]
            if name in ('primary.sql', 'primary-rollback.sql'):
                known.append(legacy.render_sql(base_report['sql_rows'], name.endswith('rollback.sql')).encode())
            elif name in ('optional.sql', 'optional-rollback.sql'):
                main, skins, forest = split_rows(base_report)
                known.append(render_sql(skins, 'optional', name.endswith('rollback.sql'),
                                        prerequisites=() if name.endswith('rollback.sql') else forest + main).encode())
            require(dest.read_bytes() in known, 'Refusing unknown SQL: ' + str(dest))
        replacements[dest] = output / name
    for dest in replacements:
        require(not dest.is_symlink(), 'Linked destination: ' + str(dest))
        require(not any(p.is_symlink() for p in dest.parents), 'Linked destination parent')
        require(not any(p.exists() and not p.is_dir() for p in dest.parents),
                'Non-directory destination ancestor: ' + str(dest))
        staging = dest.with_name(dest.name + '.tmp')
        require(not staging.exists() and not staging.is_symlink(), 'Stale publish staging file: ' + str(staging))
    # Stage everything (including v2) before replacing any current artifact.
    for dest, source in replacements.items():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest.with_name(dest.name + '.tmp'))
    # Archive is finalized first; source bytes have already all been staged.
    for dest in sorted(replacements, key=lambda p: (not p.is_relative_to(archive), str(p))):
        dest.with_name(dest.name + '.tmp').replace(dest)
    verify_base(archive)
    legacy.verify_publication(package)
    legacy.verify_publication(package / 'optional-extra-skins')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--base-version', choices=('sources', 'current'), default='sources')
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    results = build(args.output, args.base_version)
    if args.publish:
        publish(args.output)
    print(json.dumps({k: dict(counts=v['counts'], patch_sha256=v['patch_sha256']) for k, v in results.items()}, indent=2))


if __name__ == '__main__':
    main()
