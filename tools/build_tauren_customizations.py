#!/usr/bin/env python3
"""Extend the pinned accepted Troll editions; original clients are read-only.

Delivery: client_patches/{Data,archive/optional-extra-skins/Data}/patch-S.MPQ.
Principal means complete ordinary-face coverage; fixed-face looks are optional.
No SQL/runtime/client installation is performed by this builder.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tempfile

import numpy as np

import build_troll_customizations as codec
import build_troll_patch_editions as editions
from build_troll_face_format_test import palette_encode
from crypt_release_client import members, key
from tauren_geosets import convert as convert_geosets

ROOT = codec.ROOT
RECIPE = ROOT / 'tools/tauren-customizations.json'
SECTION = r'DBFilesClient\CharSections.dbc'
STYLES = r'DBFilesClient\CharacterFacialHairStyles.dbc'
HAIRS = r'DBFilesClient\CharHairGeosets.dbc'
NAMESPACE = 'Character\\Custom\\TurtleTauren'
require, digest, sha = codec.require, codec.digest, codec.sha
PRODUCTS = ('Data/patch-S.MPQ', 'report.json', 'SHA256SUMS')
BASE_PATHS = {
    'primary': 'client_patches/turtle_forest_troll',
    'optional': 'client_patches/turtle_forest_troll/optional-extra-skins',
}


def base_directory(logical_path):
    """Keep recipe/report identities stable; read relocated inputs only from archive."""
    paths = {
        BASE_PATHS['primary']: 'client_patches/archive/source-inputs/turtle_forest_troll',
        BASE_PATHS['optional']: 'client_patches/archive/turtle_forest_troll/optional-extra-skins',
    }
    require(logical_path in paths, 'Unknown Troll baseline path ' + str(logical_path))
    return ROOT / paths[logical_path]


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def capture(audit):
    """One-time research handoff; build never consumes the audit directory."""
    require(not RECIPE.exists(), 'Recipe already exists')
    d = json.loads((audit / 'audit.json').read_text())
    wanted = {'turtle': set(), '335': set()}
    source = d['turtle']['tables']['CharSections']['rows']
    full = [r for r in source if r['base'] in (0, 1, 4) and r['flags'] == 0
            and r['color'] == (19 if r['sex'] == 0 else 11)]
    for r in full + [r for r in source if r['base'] == 0 and r['flags'] == 1]:
        wanted['turtle'].update(n.lower() for n in r['textures'] if n)
    wanted['turtle'].add(r'textures\bakednpctextures\spiritwalkertaurenshop.blp')
    wanted['turtle'].update(rf'character\tauren\scalplowerhair00_{c:02}.blp' for c in range(3, 9))
    for sex in ('male', 'female'):
        model = rf'character\tauren\{sex}\tauren{sex}.m2'
        wanted['turtle'].add(model)
        wanted['335'].add(model)
        wanted['335'].update(model[:-3] + f'{i:02}.skin' for i in range(3))
        for c in range(6):
            wanted['335'].update(rf'character\tauren\{sex}\tauren{sex}{part}00_{c:02}.blp'
                                 for part in ('skin', 'nakedpelvisskin'))
            if sex == 'female':
                wanted['335'].add(rf'character\tauren\female\taurenfemalenakedtorsoskin00_{c:02}.blp')
    archives, assets = {}, {}
    def pin(client, entry):
        archive = Path(entry['archive'])
        root = Path('/home/dev/wow-turtle' if client == 'turtle' else '/home/dev/wow-335')
        label = client + ':' + archive.relative_to(root).as_posix()
        if label not in archives:
            archives[label] = dict(client=client, path=archive.relative_to(root).as_posix(), sha256=sha(archive))
        return label
    for client in wanted:
        for name in sorted(wanted[client]):
            r = d[client]['resources'][name]
            require(r.get('candidates'), 'Missing required source ' + name)
            e = r['candidates'][0]
            assets[client + ':' + name] = dict(archive=pin(client, e), member=e['member'], sha256=r['sha256'])
        for table in ('CharSections', 'CharHairGeosets', 'CharacterFacialHairStyles'):
            e = d[client]['tables'][table]['source']
            assets[client + ':table:' + table] = dict(archive=pin(client, e), member=e['name'], sha256=e['sha256'])
    bases = {}
    for edition, logical_path in BASE_PATHS.items():
        directory = base_directory(logical_path)
        bases[edition] = dict(path=logical_path,
                              files={n: sha(directory / n) for n in PRODUCTS})
    write_json(RECIPE, dict(version=1, race=6, archives=archives, assets=assets, bases=bases,
        primary_colors={'male': 25, 'female': 17}, optional_colors={'male': [26, 27, 28], 'female': [18, 19]},
        ids={'primary_first': 21000, 'primary_last': 21162, 'optional_first': 21200, 'optional_last': 21214},
        policy='Complete ordinary face bank is principal; one-face bakes optional. DK-exclusive faces are not fabricated.',
        decisions={'hair': 'Preserve NPC color3; source scalp-lower3..8 maps to new4..9. Texture1/3 placeholders are unused by native Tauren materials and remain empty in new rows.',
                   'shop': 'Male shop has one baked face and aliases the blue19 extra-skin texture; classify optional, not a full-face family.',
                   'geometry': 'Port only missing weighted facial pieces; referenced bone hierarchy/bind pivots must match and native animation prefix stays intact.'},
        geometry='Append missing facial sections with verified unchanged weighted skeleton; retain native animation data.',
        garment_limits={'male_NakedPelvisSkin': [2.46, 15], 'female_NakedPelvisSkin': [3.28, 21],
                        'female_NakedTorsoSkin': [5.20, 34]}))


def sql(rows, optional=False, rollback=False, prerequisites=(), dependents=()):
    text = editions.render_sql(rows, 'optional' if optional else 'primary', rollback,
                               prerequisites=prerequisites, dependents=dependents)
    old = 'troll_extra_skins' if optional else 'troll_primary'
    new = 'tauren_extra_skins' if optional else 'tauren_primary'
    return text.replace(old, new).replace('tools/build_troll_patch_editions.py', 'tools/build_tauren_customizations.py').replace(
        'Optional skins require exact Forest90 and primary208', 'Optional Tauren requires exact principal prerequisites')


def build(output):
    m = json.loads(RECIPE.read_text())
    output = Path(output).resolve()
    require(not output.exists(), 'Fresh output required')
    require(output.is_relative_to((ROOT / 'work').resolve()), 'Build output must be under work/')
    require(np.__version__ == '2.2.6', 'Use pinned customization requirements')
    roots = {'turtle': Path('/home/dev/wow-turtle'), '335': Path('/home/dev/wow-335')}
    archive_paths = {}
    for label, spec in m['archives'].items():
        path = roots[spec['client']] / spec['path']
        require(sha(path) == spec['sha256'], 'Source archive mismatch ' + str(path))
        archive_paths[label] = path
    old = {}
    oldreports = {}
    for edition, spec in m['bases'].items():
        directory = base_directory(spec['path'])
        for name, h in spec['files'].items():
            require(sha(directory / name) == h, 'Troll baseline changed ' + name)
        old[edition] = {name: raw for name, raw in members(codec.forest.MPQ, directory / PRODUCTS[0]).values()}
        oldreports[edition] = json.loads((directory / 'report.json').read_text())
    output.mkdir(parents=True)
    provenance, resources = {}, {}
    with tempfile.TemporaryDirectory(prefix='tauren-build-') as temp:
        stage = Path(temp)
        cache = {}
        def get(client, name):
            label = client + ':' + name.lower() if not name.startswith('table:') else client + ':' + name
            if label not in cache:
                spec = m['assets'][label]
                raw = codec.forest.extract(archive_paths[spec['archive']], spec['member'], stage / 'extract')
                require(digest(raw) == spec['sha256'], 'Resource hash mismatch ' + name)
                cache[label] = raw
                provenance[label] = spec
            return cache[label]
        def relocated(name):
            if not name:
                return ''
            return name.replace('Character\\Tauren', NAMESPACE, 1)
        def copy(name):
            if not name:
                return ''
            target = relocated(name)
            raw = get('turtle', name)
            codec.forest.validate_blp(raw)
            resources[target] = raw
            return target
        generated = []
        def image(target, rgba):
            raw, metrics = palette_encode(codec.encode_blp(rgba), allow_quantize=True)
            resources[target] = raw
            generated.append(dict(member=target, **metrics))
            return target
        raw = get('turtle', 'table:CharSections')
        sr, ss = codec.forest.read_dbc(raw)
        source = [codec.forest.decode(r, ss, 'turtle') for r in sr if r[1] == 6]
        native_raw = get('335', 'table:CharSections')
        nr, ns = codec.forest.read_dbc(native_raw)
        # Fresh ordinary skins have full authored face banks, not aliases.
        new_main = []
        full_proof = []
        for sex in (0, 1):
            sc, tc, faces = (19, 25, 5) if sex == 0 else (11, 17, 4)
            chosen = [r for r in source if r[2] == sex and r[3] in (0, 1, 4) and r[7] == 0 and r[9] == sc]
            require(len(chosen) == faces + 2 and {r[8] for r in chosen if r[3] == 1} == set(range(faces)),
                    'Incomplete full-face skin')
            pairs = {tuple(codec.decode_blp(get('turtle', name)).tobytes() for name in r[4:6])
                     for r in chosen if r[3] == 1}
            require(len(pairs) == faces, 'Face bank aliases cannot be classified complete')
            for r in chosen:
                new_main.append((0, *r[1:4], *(copy(n) for n in r[4:7]), 17, r[8], tc))
            full_proof.append(dict(sex=sex, source_color=sc, target_color=tc,
                                   distinct_authored_faces=faces, source_ids=[r[0] for r in chosen]))
        # Native horn styles already exist: expose barber rows, keep all meshes.
        hair_overrides = []
        for r in nr:
            if r[1] == 6 and r[3] == 3 and r[7] == 0x12:
                hair_overrides.append((*codec.forest.decode(r, ns)[:7], 0x13, *r[8:]))
        require(len(hair_overrides) == 30, 'Expected30 native barber unlocks')
        # The racial models have no hair texture type6; source Texture1/3 are
        # missing/legacy placeholders. Only the authored scalp-lower layer is used.
        for sex, styles in ((0, 13), (1, 12)):
            for variation in range(styles):
                for color in range(4, 10):
                    texture = copy(rf'Character\Tauren\ScalpLowerHair00_{color-1:02}.blp')
                    new_main.append((0, 6, sex, 3, '', texture, '', 17, variation, color))
        new_main = [(21000+i, *r[1:]) for i, r in enumerate(sorted(new_main, key=codec.forest.key))]
        require(len(new_main) == 163 and new_main[-1][0] == 21162, 'Principal allocation changed')
        primary_rows = sorted(new_main + hair_overrides, key=codec.forest.key)

        # Native garment masks are only needed by incomplete baked skins.
        fitted, garment = {}, []
        for sex, label in enumerate(('Male', 'Female')):
            for component, box in [('NakedPelvisSkin', [256,192,512,320])] + (
                    [('NakedTorsoSkin', [256,0,512,128])] if sex else []):
                bodies, clothes = [], []
                for color in range(6):
                    stem = rf'Character\Tauren\{label}\Tauren{label}'
                    b = codec.decode_blp(get('335', stem + f'Skin00_{color:02}.blp'))
                    u = codec.decode_blp(get('335', stem + f'{component}00_{color:02}.blp'))
                    bodies.append(codec.crop(b, box)[:, :, :3]); clothes.append(u[:, :, :3])
                bounds = m['garment_limits'][label.lower() + '_' + component]
                f, a, proof = codec.fit_garment(bodies, clothes, dict(mae_max=bounds[0], p99_max=bounds[1]))
                fitted[sex, component] = f, a, box
                garment.append(dict(sex=sex, component=component, **proof))
        optional_resources, optional_rows, partial_proof = {}, [], []
        for sex, label in enumerate(('Male', 'Female')):
            chosen = [r for r in source if r[2] == sex and r[3] == 0 and r[7] == 1]
            require(len(chosen) == 2, 'Expected blue and GrimTotem bodies')
            candidates = [(str(r[0]), r[4], r[5], r[0]) for r in chosen]
            if sex == 0:
                candidates.append(('spiritwalkershop', r'textures\bakednpctextures\spiritwalkertaurenshop.blp',
                                   chosen[0][5], None))
            for color, (name, bodyname, extraname, sid) in enumerate(candidates, 26 if sex == 0 else 18):
                prefix = rf'{NAMESPACE}\{label}\Partial{name}'
                body, extra = get('turtle', bodyname), get('turtle', extraname)
                target = prefix + '_Body.blp'; optional_resources[target] = body
                etarget = prefix + '_Extra.blp'; optional_resources[etarget] = extra
                atlas = codec.decode_blp(body)
                require(atlas.shape == (256,256,4), 'Expected256 source bake')
                atlas = atlas.repeat(2, 0).repeat(2, 1)
                before = set(resources)
                lower = image(prefix + '_FaceLower.blp', codec.crop(atlas, [0,384,256,512]))
                upper = image(prefix + '_FaceUpper.blp', codec.crop(atlas, [0,320,256,384]))
                cloth = []
                for component in ('NakedPelvisSkin',) + (('NakedTorsoSkin',) if sex else ()):
                    f, a, box = fitted[sex, component]
                    rgba = codec.crop(atlas, box)
                    rgba[:, :, :3] = np.rint(a*f+(1-a)*rgba[:, :, :3]).clip(0,255).astype(np.uint8)
                    cloth.append(image(prefix + '_' + component + '.blp', rgba))
                for n in set(resources) - before:
                    optional_resources[n] = resources.pop(n)
                optional_rows += [(0,6,sex,0,target,etarget,'',17,0,color),
                                  (0,6,sex,1,lower,upper,'',17,0,color),
                                  (0,6,sex,4,cloth[0],cloth[1] if sex else '','',17,0,color)]
                partial_proof.append(dict(sex=sex, color=color, source_id=sid,
                    source_body=bodyname, extra_texture_source=extraname,
                    shop_extra_alias=(sid is None), face_variations=[0], full_face_compatible=False))
        optional_rows = [(21200+i, *r[1:]) for i, r in enumerate(sorted(optional_rows, key=codec.forest.key))]
        require(len(optional_rows) == 15, 'Optional allocation changed')
        # Model append only: no skeleton or animation conversion.
        geometry = []
        for sex, label in enumerate(('Male','Female')):
            member = rf'Character\Tauren\{label}\Tauren{label}.m2'
            source_model, native_model = get('turtle', member), get('335', member)
            skins = [get('335', member[:-3] + f'{i:02}.skin') for i in range(3)]
            modified, profiles, proof = convert_geosets(source_model, native_model, skins, sex)
            resources[member] = modified
            for i, profile in enumerate(profiles):
                resources[member[:-3] + f'{i:02}.skin'] = profile
            geometry.append(dict(sex=sex, **proof))
        natural = [(6,0,7,10,10,10,0,0),(6,0,8,11,11,11,0,0),
                   (6,1,5,0,0,6,0,0),(6,1,6,0,0,7,0,0)]
        source_styles = codec.read_numeric(get('turtle','table:CharacterFacialHairStyles'), 9)
        require(sorted([(*r[:3], *r[6:9],0,0) for r in source_styles if r[:3] in [x[:3] for x in natural]]) == natural,
                'Source facial geometry mappings changed')
        # Hair geoset keys and values already exist identically in Wrath.
        sh = codec.read_numeric(get('turtle','table:CharHairGeosets'),6)
        nh = codec.read_numeric(get('335','table:CharHairGeosets'),6)
        require({tuple(r[1:4]):r[4:] for r in sh if r[1]==6} ==
                {tuple(r[1:4]):r[4:] for r in nh if r[1]==6}, 'Hair geometry mapping differs')
        oldpr = oldreports['primary']
        troll_prereq = oldpr['sql_rows'] + [[r['target_id'],r['race'],r['sex'],r['base'],*r['textures'],r['flags'],r['variation'],r['color']]
                                          for r in oldpr['source_to_target']]
        sqls = {'primary.sql': sql(primary_rows),
                'primary-rollback.sql': sql(primary_rows, rollback=True, dependents=optional_rows),
                'optional.sql': sql(optional_rows, optional=True, prerequisites=troll_prereq+primary_rows),
                'optional-rollback.sql': sql(optional_rows, optional=True, rollback=True)}
        for name, text in sqls.items():
            (output / name).write_text(text)
        common_styles = codec.read_numeric(old['primary'][STYLES],8)
        require(not {r[:3] for r in common_styles}.intersection(r[:3] for r in natural), 'Facial key collision')
        merged_styles = codec.numeric_dbc(common_styles + natural,8)
        old_donor = (ROOT / 'data/server/turtle-customizations/dbc/CharacterFacialHairStyles.dbc').read_bytes()
        donor_rows = codec.read_numeric(old_donor,8)
        # Accept already-updated source donor on deterministic rebuilds.
        donor_rows = [r for r in donor_rows if r[0] != 6]
        troll_keys = {(8,0,v) for v in (11,12,13)} | {(8,1,v) for v in (6,7,8,9)}
        require(sorted(donor_rows) == sorted(r for r in common_styles if r[:3] in troll_keys),
                'Expected exact seven Troll donor rows')
        donor_raw = codec.numeric_dbc(sorted(donor_rows+natural),8)
        (output / 'CharacterFacialHairStyles.delta.dbc').write_bytes(donor_raw)
        server_manifest = json.loads((ROOT/'data/server/manifest.json').read_text())
        donor_entry = server_manifest['files']['turtle-customizations/dbc/CharacterFacialHairStyles.dbc']
        donor_entry.update(size=len(donor_raw), sha256=digest(donor_raw))
        write_json(output/'server-manifest.json',server_manifest)
        result = {}
        for edition in ('primary','optional'):
            payload = dict(old[edition]); payload.update(resources)
            rows, block = codec.forest.read_dbc(payload[SECTION])
            byid = {r[0]:r for r in rows}
            for r in hair_overrides:
                previous = byid[r[0]]
                require(codec.forest.decode(previous,block)[:7] == r[:7] and previous[7] == 0x12, 'Hair override conflict')
                byid[r[0]] = (*previous[:7],0x13,*previous[8:])
            changed = [byid[r[0]] for r in rows]
            additions = sorted(new_main+(optional_rows if edition=='optional' else []), key=codec.forest.key)
            full, _ = codec.forest.merge(changed,block,additions)
            payload[SECTION], payload[STYLES] = full, merged_styles
            if edition == 'optional':
                payload.update(optional_resources)
            directory = output / edition
            (directory/'Data').mkdir(parents=True)
            patch = directory/PRODUCTS[0]
            codec.create_mpq(patch,payload,stage)
            repeat = stage/(edition+'-repeat.MPQ'); codec.create_mpq(repeat,payload,stage)
            require(sha(patch)==sha(repeat), 'Non-deterministic output')
            for name, raw in old[edition].items():
                if name not in (SECTION,STYLES):
                    require(payload[name] == raw, 'Troll texture or resource modified')
            report = dict(version=1, edition=edition, recipe_sha256=sha(RECIPE), base=m['bases'][edition],
                patch_sha256=sha(patch), charsections_sha256=digest(full),natural_styles_sha256=digest(merged_styles),
                primary_rows=primary_rows,optional_rows=optional_rows,full_face_skins=full_proof,
                fixed_face_skins=partial_proof if edition=='optional' else [],
                geometry=geometry,garment_reconstruction=garment,generated_images=generated if edition=='optional' else [],
                provenance=provenance,server_donor_sha256=digest(donor_raw),
                server_manifest_sha256=sha(output/'server-manifest.json'),
                counts=dict(charsections=len(codec.forest.read_dbc(full)[0]),
                    natural_styles=233,primary_sql=193,optional_sql=15,new_hair_colors=6,
                    barber_unlocks=30,full_face_skins=2,fixed_face_skins=5 if edition=='optional' else 0,
                    new_facial_styles=4,payload_members=len(payload)),
                preservation=dict(troll_resources_byte_exact=True,old_indices_not_renumbered=True,
                                  native_model_animation_prefix_preserved=True),
                validations=dict(client_runtime=False,live_db_changed=False),
                sql_sha256={name:digest(text.encode()) for name,text in sqls.items()})
            write_json(directory/'report.json',report)
            (directory/'SHA256SUMS').write_text(''.join(f'{sha(directory/n)}  {n}\n' for n in PRODUCTS[:2]))
            result[edition]=report
        return result


def publish(output):
    targets={'primary': ROOT/'client_patches', 'optional': ROOT/'client_patches/archive/optional-extra-skins'}
    files={}
    for edition,target in targets.items():
        source=output/edition
        codec.verify_publication(source)
        report=json.loads((source/'report.json').read_text())
        require(report['recipe_sha256']==sha(RECIPE) and sha(source/PRODUCTS[0])==report['patch_sha256'], 'Output mismatch')
        require(all(sha(output/name)==h for name,h in report['sql_sha256'].items()), 'SQL output changed')
        require(sha(output/'CharacterFacialHairStyles.delta.dbc')==report['server_donor_sha256'], 'Donor output changed')
        require(sha(output/'server-manifest.json')==report['server_manifest_sha256'], 'Server manifest output changed')
        for name in PRODUCTS:
            files[target/name]=source/name
    names={'primary.sql':'data/sql/custom/db_world/turtle_tauren_customizations.sql',
           'primary-rollback.sql':'data/sql/rollback/turtle_tauren_customizations.sql',
           'optional.sql':'data/sql/optional/db_world/turtle_tauren_extra_skins.sql',
           'optional-rollback.sql':'data/sql/rollback/turtle_tauren_extra_skins.sql',
           'CharacterFacialHairStyles.delta.dbc':'data/server/turtle-customizations/dbc/CharacterFacialHairStyles.dbc',
           'server-manifest.json':'data/server/manifest.json'}
    for source,target in names.items():
        files[ROOT/target]=output/source
    for dest,src in files.items():
        if dest.exists():
            identical=dest.read_bytes()==src.read_bytes()
            old_donor=(dest.name=='CharacterFacialHairStyles.dbc' and sha(dest)==
                       '32cb5d24ac98286aeba6aa20952852fd5b25afd97e39cd6035c499a7f8ba16cf')
            manifest_upgrade=False
            if dest==ROOT/'data/server/manifest.json':
                before=json.loads(dest.read_text()); after=json.loads(src.read_text())
                k='turtle-customizations/dbc/CharacterFacialHairStyles.dbc'
                prior=before['files'].get(k,{})
                expected_old=dict(after['files'][k],size=245,sha256=
                    '32cb5d24ac98286aeba6aa20952852fd5b25afd97e39cd6035c499a7f8ba16cf')
                require(prior in (after['files'][k],expected_old), 'Unknown server donor manifest entry')
                before['files'][k]=after['files'][k]
                manifest_upgrade=before==after
            require(identical or old_donor or manifest_upgrade, 'Refusing different destination '+str(dest))
        require(not any(p.is_symlink() for p in (dest,*dest.parents)), 'Symlink output')
        require(not any(p.exists() and not p.is_dir() for p in dest.parents), 'Non-directory output parent')
        require(not dest.with_name(dest.name+'.tmp').exists(), 'Stale publication temporary')
    for dest,src in files.items():
        dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dest.with_name(dest.name+'.tmp'))
    for dest in files:
        dest.with_name(dest.name+'.tmp').replace(dest)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path)
    p.add_argument('--capture-audit',type=Path)
    p.add_argument('--publish',action='store_true')
    a=p.parse_args()
    if a.capture_audit:
        capture(a.capture_audit)
    else:
        if not a.output:p.error('--output required')
        reports=build(a.output)
        if a.publish:publish(a.output)
        print(json.dumps({k:dict(counts=v['counts'],patch_sha256=v['patch_sha256']) for k,v in reports.items()},indent=2))
