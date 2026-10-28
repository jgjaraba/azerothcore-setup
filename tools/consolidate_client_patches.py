#!/usr/bin/env python3
"""Pinned member-allowlisted delivery. --freeze INVENTORY creates the source lock.

--output DIR --reproducible --publish builds twice, reads back and publishes.
--verify client_patches independently checks the delivery against pinned sources.
No archive directory is ever recursively consumed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

from crypt_release_dbc import merge_dbc, parse_dbc, semantic_row, string_at
from crypt_release_client import DBC_DELTAS
from high_elf_eye_selectors import eye_models, fix_selectors
from high_elf_eye_opacity import member as eye_member, normalize_eye_opacity

ROOT = Path(__file__).resolve().parent.parent
MPQ = ROOT / 'tools/mpq'
LOCK = ROOT / 'tools/client-patches-sources.json'
META = {'(listfile)', '(attributes)', '(signature)'}
PRIMARY = 'client_patches/Data/patch-S.MPQ'
NEW = 'client_patches/new-races/primary/Data/patch-Z.mpq'
CRYPT = 'client_patches/turtle_crypt/r5-coordinated/Data/patch-T.MPQ'
REG = 'client_patches/regular_client/patch-Z.mpq'
HD = 'client_patches/hd_client/patch-Z.mpq'
ARCHIVE_DIRS = ('optional-extra-skins', 'new-races/optional-extra-skins',
                'turtle_forest_troll/optional-extra-skins', 'turtle_forest_troll/face-format-test', 'turtle_forest_troll/v2')
LOCALIZED = {'chrraces', 'map', 'areatable', 'mapdifficulty', 'spell', 'wmoareatable'}
# ChrRaces field7 is numeric TeamID, NOT a string offset. ClientFileString is
# field11: native Glue uses it for background/ambience and race icon selection.
STRINGS = {'chrraces': [6, 11, *range(14, 30), *range(31, 47), *range(48, 64), 65, 66, 67],
           'creaturedisplayinfo': [6, 7, 8], 'creaturedisplayinfoextra': [20],
           'creaturemodeldata': [2], 'charsections': [4, 5, 6],
           'spell': [*range(136, 152), *range(153, 169), *range(170, 186), *range(187, 203)]}
for _name, (_, _, _strings, _) in DBC_DELTAS.items():
    STRINGS[_name[:-4].lower()] = _strings
STRINGS['mapdifficulty'] = [*range(3, 19), 22]  # trailing internal difficulty name
STRINGS['wmoareatable'] = list(range(11, 27))
STRINGS['worldmapoverlay'] = [8]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pinned_path(source, spec):
    """Resolve only the explicit physical input; logical source IDs are provenance."""
    path = ROOT / spec['path']
    require(path.is_file(), f'Missing source input: {source}: {path}; '
            f'recover the pinned baseline (SHA256 {spec["sha256"]}) at this path')
    require(file_sha(path) == spec['sha256'], f'Source archive changed: {source}: {path}')
    return path


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def norm(name):
    value = name.replace('\\', '/').lower()
    require(all(p and p not in ('.', '..') and ':' not in p for p in value.split('/'))
            and not any(ord(c) < 32 or c == '|' for c in value), 'Unsafe member name')
    return value


def run(*args):
    return subprocess.run([str(MPQ), *map(str, args)], check=True, capture_output=True).stdout


def listing(path):
    names = [line.rsplit('\t', 1)[0] for line in run('list', path).decode().splitlines()]
    keys = [norm(n) for n in names]
    require(len(set(keys)) == len(keys), f'Duplicate names: {path}')
    require(not any(n.startswith('file000') for n in keys), f'Unresolved names: {path}')
    return {norm(n): n for n in names if n.lower() not in META}


def extract(path, name, optional=False):
    with tempfile.TemporaryDirectory(prefix='consolidate-read-') as tmp:
        dest = Path(tmp) / 'member'
        p = subprocess.run([str(MPQ), 'extract-one', str(path), name, str(dest)], capture_output=True)
        if optional and p.returncode and p.stderr.strip() == b'ERROR: file not found in archive':
            return None
        require(p.returncode == 0, f'Cannot extract {path}: {name}: {p.stderr!r}')
        return dest.read_bytes()


def category(name):
    name = norm(name)
    if name.startswith('dbfilesclient/'):
        return 'dbc'
    if name.startswith('character/'):
        return 'characters'
    if name.startswith(('world/', 'textures/minimap/', 'interface/worldmap/', 'interface/glues/loading')):
        return 'geography'
    if 'darkrider' in name:
        return 'dark-rider'
    return 'glue-login' if name.startswith(('interface/', 'sound/')) else 'geography'


class Sources:
    def __init__(self, lock):
        self.lock, self.cache, self.verified = lock, {}, set()

    def get(self, source):
        if source.startswith('high-elf-map:'):
            from package_high_elf_map import source_members
            if source not in self.cache:
                self.cache[source] = source_members(source)
            return self.cache[source]
        if source not in self.cache:
            spec = self.lock['sources'][source]
            path = ROOT / spec['path']
            if str(path) not in self.verified:
                pinned_path(source, spec)
                self.verified.add(str(path))
            if not spec.get('subset'):
                require(set(listing(path)) == set(spec['members']), f'Source inventory changed: {path}')
            data = {}
            for key, entry in spec['members'].items():
                raw = extract(path, entry['name'])
                require(sha(raw) == entry['sha256'] and len(raw) == entry['size'], f'Source member changed: {key}')
                data[key] = (entry['name'], raw)
            self.cache[source] = data
        return self.cache[source]


def rows(raw, table):
    """Semantic rows, including the two packed Wrath schemas."""
    count, fields, size, length = struct.unpack_from('<4I', raw, 4)
    require(raw[:4] == b'WDBC' and len(raw) == 20 + count * size + length, 'Bad WDBC')
    if table == 'charbaseinfo':
        require((fields, size) == (2, 2), 'Wrong CharBaseInfo schema')
        return {tuple(raw[20+i*2:22+i*2]): tuple(raw[20+i*2:22+i*2]) for i in range(count)}
    if table == 'charstartoutfit':
        require((fields, size) == (77, 296), 'Wrong CharStartOutfit schema')
        values = [struct.unpack_from('<I4B72I', raw, 20+i*size) for i in range(count)]
        return {r[0]: r for r in values}
    if table == 'characterfacialhairstyles':
        require((fields, size) == (8, 32), 'Wrong facial-style schema')
        values = [struct.unpack_from('<8I', raw, 20+i*size) for i in range(count)]
        require(len({r[:3] for r in values}) == count, 'Duplicate facial-style keys')
        return {r[:3]: r for r in values}
    _, values, strings = parse_dbc(raw)
    return {r[0]: semantic_row(r, strings, STRINGS.get(table, [])) for r in values}


def record_diff(base, result, table):
    a, b = rows(base, table), rows(result, table)
    convert = lambda ids: sorted(str(i) for i in ids)
    return {'added': convert(b.keys() - a.keys()), 'removed': convert(a.keys() - b.keys()),
            'changed': convert(i for i in a.keys() & b.keys() if a[i] != b[i]),
            'preserved': sum(a[i] == b[i] for i in a.keys() & b.keys())}


def encode(fields, records, strings):
    return struct.pack('<4s4I', b'WDBC', len(records), fields, fields*4, len(strings)) + b''.join(
        struct.pack(f'<{fields}I', *r) for r in records) + bytes(strings)


def localized_races(native, donor, locale):
    fields, source, source_strings = parse_dbc(donor)
    _, original, native_strings = parse_dbc(native)
    natives = {r[0]: r for r in original}
    block = bytearray(b'\0')
    offsets = {b'': 0}
    result = []
    for record in source:
        row = record.copy()
        for col in STRINGS['chrraces']:
            names = col in {*range(14, 30), *range(31, 47), *range(48, 64)}
            text = string_at(native_strings, natives[row[0]][col]) if names and row[0] in natives else string_at(source_strings, row[col])
            # Supply locale-appropriate default-name fallbacks while keeping every
            # authored Spanish bank. This cannot compensate for root-Z masking:
            # localized tables must be owned exclusively by the locale archives.
            if locale == 'esES' and row[0] in natives and col in (14, 31, 48) and not text:
                text = string_at(native_strings, natives[row[0]][col+6])
            if row[0] in (22, 23) and col in (14, 31, 48, 20, 37, 54):
                text = ('High Elf' if locale == 'enUS' and col in (14, 31, 48) else 'Alto Elfo').encode() if row[0] == 22 else b'Goblin'
            if text not in offsets:
                offsets[text] = len(block)
                block.extend(text + b'\0')
            row[col] = offsets[text]
        result.append(row)
    return encode(fields, result, block)


def freeze(inventory):
    """Create an explicit immutable source/member lock from the research inventory."""
    require(not LOCK.exists(), 'Lock exists; review changes explicitly instead of refreezing')
    inventory = json.loads(Path(inventory).read_text())
    selected = [PRIMARY, NEW, CRYPT, REG, HD, 'client_patches/patch-enUS-Z.MPQ', 'client_patches/patch-esES-Z.MPQ']
    result = {'version': 1, 'sources': {}, 'excluded_inventory': {}, 'relocations': {},
              'profiles': ['regular_client', 'hd_client'], 'launcher_profiles': ['regular_client'],
              'native_model_closure': {}, 'native_model_closure_usage': 'research only; not an active dependency'}
    for source, entries in inventory.items():
        destination = source
        if source in (REG, HD):
            destination = source.replace('client_patches/', 'client_patches/archive/baselines/', 1)
        if source not in selected:
            result['excluded_inventory'][source] = entries
            continue
        result['sources'][source] = {'path': destination, 'sha256': file_sha(ROOT/source),
            'members': {norm(k): {k2: v for k2, v in entry.items() if k2 != 'header'}
                        for k, entry in entries.items() if k.lower() not in META}}
        if destination != source:
            result['relocations'][source] = destination
    native_manifest = json.loads((ROOT/'tools/new-races-assets.json').read_text())
    archives = []
    for rel in json.loads((ROOT/'tools/crypt-release-stock-eses.json').read_text()):
        if not rel.startswith('esES/'):
            archives.append('/home/dev/wow-335/Data/' + rel)
    for locale in ('enUS', 'esES'):
        suffix = 'MPQ' if locale == 'enUS' else 'mpq'
        for name in (f'locale-{locale}', f'expansion-locale-{locale}', f'lichking-locale-{locale}',
                     f'patch-{locale}', f'patch-{locale}-2', f'patch-{locale}-3'):
            path = Path('/home/dev/wow-335/Data')/locale/(name + '.' + suffix)
            if not path.exists():
                path = path.with_name(path.name.lower())
            require(str(path) in native_manifest['archives'], f'Unpinned native archive: {path}')
            if str(path) not in archives:
                archives.append(str(path))
    verified = set()
    def native(name, locale=None):
        candidates = [a for a in archives if '/enUS/' not in a and '/esES/' not in a or locale and f'/{locale}/' in a]
        for archive in reversed(candidates):
            raw = extract(archive, name, optional=True)
            if raw is None:
                continue
            if archive not in verified:
                require(file_sha(archive) == native_manifest['archives'][archive], f'Native archive changed: {archive}')
                verified.add(archive)
            key = 'native:' + (locale + ':' if locale else '') + norm(name)
            result['sources'][key] = {'path': archive, 'sha256': native_manifest['archives'][archive],
                'subset': True, 'members': {norm(name): {'name': name, 'sha256': sha(raw), 'size': len(raw)}}}
            return key, raw
        raise ValueError(f'Missing native dependency: {name}')
    for locale in ('enUS', 'esES'):
        for name in ('ChrRaces', 'Map', 'AreaTable', 'MapDifficulty'):
            native('DBFilesClient\\' + name + '.dbc', locale)
    for sex in ('Male', 'Female'):
        name = f'Character\\Tauren\\{sex}\\Tauren{sex}.m2'
        entry = inventory[PRIMARY][norm(name)]
        raw = extract(ROOT/PRIMARY, entry['name'])
        dependencies = []
        count, offset = struct.unpack_from('<2I', raw, 28)
        require(offset + count*64 <= len(raw), 'Bad M2 animation array')
        for i in range(count):
            ident, sub = struct.unpack_from('<2H', raw, offset+i*64)
            flags, = struct.unpack_from('<I', raw, offset+i*64+12)
            if flags & (0x20 | 0x40):
                continue
            dependency = name[:-3] + f'{ident:04d}-{sub:02d}.anim'
            key, _ = native(dependency)
            dependencies.append(key)
        count, offset = struct.unpack_from('<2I', raw, 80)
        for i in range(count):
            kind, _, length, pos = struct.unpack_from('<4I', raw, offset+i*16)
            if kind == 0 and length:
                dependency = raw[pos:pos+length].rstrip(b'\0').decode()
                key, _ = native(dependency)
                dependencies.append(key)
        result['native_model_closure'][norm(name)] = sorted(set(dependencies))
    launcher = 'client_patches/new-races/Wow-new-races.exe'
    result['launcher'] = {'path': launcher, 'sha256': file_sha(ROOT/launcher)}
    dump(LOCK, result)


def plan(lock, sources, include_high_elf=True):
    result = {}
    def add(package, name, raw, provenance):
        result.setdefault(package, {})[norm(name)] = {'name': name, 'data': raw, 'provenance': provenance,
                                                     'category': category(name)}
    def copy(package, source, key):
        name, raw = sources.get(source)[key]
        add(package, name, raw, [source])
    new = {k: v for k, v in sources.get(CRYPT).items() if k.startswith('dbfilesclient/')}
    new.update(sources.get(NEW))
    origin = {k: NEW if k in sources.get(NEW) else CRYPT for k in new}
    geometry, _ = eye_models({k: raw for k, (_, raw) in sources.get(NEW).items()})
    eye_payload = {}
    for sex in ('Male', 'Female'):
        key = norm(eye_member(sex))
        eye_payload[key], _ = normalize_eye_opacity(new[key][1], new[key[:-3]+'00.skin'][1], sex)
    for profile in lock['profiles']:
        prefix = profile + '/Data/'
        if profile == 'hd_client':
            # Preserve the external HD client's historical whole-table contract. In
            # particular, never mask its unknown CreatureModelData with a stock table.
            for key in sources.get(HD):
                if key == 'dbfilesclient/itemextendedcost.dbc':
                    name, base = sources.get(HD)[key]
                    raw = merge_dbc(base, sources.get(REG)[key][1],
                                    [*range(98010, 98036), *range(99010, 99036)], [])
                    add(prefix+'patch-Z.mpq', name, raw, [HD, REG])
                else:
                    copy(prefix+'patch-Z.mpq', HD, key)
            for locale in ('enUS', 'esES'):
                copy(prefix+locale+'/patch-'+locale+'-Z.MPQ',
                     'client_patches/patch-'+locale+'-Z.MPQ', 'dbfilesclient/spell.dbc')
            continue
        old = HD if profile == 'hd_client' else REG
        for key in sources.get(PRIMARY):
            if not key.startswith('dbfilesclient/'):
                copy(prefix+'patch-S.MPQ', PRIMARY, key)
        for key in sources.get(CRYPT):
            if not key.startswith('dbfilesclient/'):
                copy(prefix+'patch-T.MPQ', CRYPT, key)
        for key in new:
            if category(key) == 'characters':
                if key in eye_payload:
                    add(prefix+'patch-S.MPQ', new[key][0], eye_payload[key], [NEW])
                else:
                    copy(prefix+'patch-S.MPQ', NEW, key)
            elif not key.startswith('dbfilesclient/') and category(key) == 'geography':
                copy(prefix+'patch-T.MPQ', NEW, key)
            elif not key.startswith('dbfilesclient/'):
                copy(prefix+'patch-Z.mpq', NEW, key)
        for key in sources.get(old):
            if not key.startswith('dbfilesclient/'):
                copy(prefix+'patch-Z.mpq', old, key)
        for key, (name, raw) in new.items():
            if not key.startswith('dbfilesclient/'):
                continue
            table = key.split('/')[-1][:-4]
            if table in LOCALIZED:
                continue
            provenance = [origin[key]]
            if table == 'characterfacialhairstyles':
                raw = fix_selectors(raw, geometry)
            add(prefix+'patch-Z.mpq', name, raw, provenance)
        for locale in ('enUS', 'esES'):
            package = prefix+locale+'/patch-'+locale+'-Z.MPQ'
            for table in ('ChrRaces', 'Map', 'AreaTable', 'MapDifficulty'):
                key = norm('DBFilesClient/'+table+'.dbc')
                native_key = 'native:'+locale+':'+key
                base = sources.get(native_key)[key][1]
                donor = new[key][1]
                if table == 'ChrRaces':
                    raw = localized_races(base, donor, locale)
                else:
                    _, ids, strings, order = DBC_DELTAS[table+'.dbc']
                    raw = merge_dbc(base, donor, ids, STRINGS[table.lower()], order)
                add(package, new[key][0], raw, [native_key, origin[key]])
            copy(package, 'client_patches/patch-'+locale+'-Z.MPQ', 'dbfilesclient/spell.dbc')
    if include_high_elf:
        from package_high_elf_map import integrate
        sources.high_elf_native = result
        return integrate(result)
    return result


def audit(planned, lock, sources):
    report = {'dbc_diffs': {}, 'legacy_spell_locale_differences': [],
              'runtime_rendering': 'NOT RUN', 'compatibility': {}, 'new_race_closure': {},
              'new_race_compositor': {}, 'feature_matrix': {}, 'external_dependencies': {},
              'package_summary': {p: {'members': len(entries),
                  'dbc_tables': sum(k.endswith('.dbc') for k in entries),
                  'payload_bytes': sum(len(e['data']) for e in entries.values())}
                  for p, entries in sorted(planned.items())}}
    for package, entries in planned.items():
        for key, entry in entries.items():
            if not key.endswith('.dbc'):
                continue
            table = key.split('/')[-1][:-4]
            for source in entry['provenance']:
                if source.startswith('high-elf-map:deltas/'):
                    # A regional delta is an input, not a full-table baseline.
                    # Report the real pre-map diff against its pinned base instead.
                    continue
                base = sources.get(source).get(key)
                if base:
                    diff = record_diff(base[1], entry['data'], table)
                    report['dbc_diffs'].setdefault(package, {}).setdefault(key, {})[source] = diff
                    if source == HD:
                        require(not diff['changed'] and not diff['removed'], f'HD records regressed: {table}')
    for profile in lock['profiles']:
        prefix = profile+'/Data/'
        master = planned[prefix+'patch-Z.mpq']
        if profile == 'hd_client':
            baseline = sources.get(HD)
            require(set(master) == set(baseline) and len(master) == 8, 'HD historical member allowlist changed')
            expected_packages = {prefix+'patch-Z.mpq', *(prefix+locale+'/patch-'+locale+'-Z.MPQ'
                                                       for locale in ('enUS', 'esES'))}
            require({p for p in planned if p.startswith(profile+'/')} == expected_packages,
                    'HD must contain exactly three conservative MPQs')
            for key, (_, base) in baseline.items():
                raw = master[key]['data']
                if key == 'dbfilesclient/itemextendedcost.dbc':
                    diff = record_diff(base, raw, 'itemextendedcost')
                    require(not diff['changed'] and not diff['removed'] and set(diff['added']) ==
                            {str(i) for i in [*range(98010, 98036), *range(99010, 99036)]},
                            'HD costs must add only the 52 accepted vendor rows')
                else:
                    require(raw == base, f'HD historical bytes changed: {key}')
            for locale in ('enUS', 'esES'):
                entries = planned[prefix+locale+'/patch-'+locale+'-Z.MPQ']
                require(set(entries) == {'dbfilesclient/spell.dbc'}, 'HD locale must contain only original Spell')
                require(entries['dbfilesclient/spell.dbc']['data'] == sources.get(
                    'client_patches/patch-'+locale+'-Z.MPQ')['dbfilesclient/spell.dbc'][1], 'HD original Spell changed')
            displays = rows(master['dbfilesclient/creaturedisplayinfo.dbc']['data'], 'creaturedisplayinfo')
            require(not set(range(91000, 91004)).intersection(displays), 'HD new-race displays are forbidden')
            require(all(r[0] not in (22, 23) for r in rows(master['dbfilesclient/charbaseinfo.dbc']['data'],
                                                        'charbaseinfo').values()), 'HD new-race class tuples forbidden')
            require(all(r[1] not in (22, 23) for r in rows(master['dbfilesclient/charstartoutfit.dbc']['data'],
                                                        'charstartoutfit').values()), 'HD new-race outfits forbidden')
            report['compatibility'][profile] = ('PRESERVED HISTORICAL HD CONTRACT; original compatible HD client required; '
                'new-race/appearance/crypt integration not included; rendering NOT RUN')
            report['feature_matrix'][profile] = {
                'historical_hd_contract': 'PRESERVED', 'additional_vendor_cost_rows': 52,
                'localized_spell_tables': 'PRESERVED COMPLETE',
                'unsupported_integrations': ['new_races_22_23', 'principal_native_customizations', 'crypt_r5',
                                             'new_race_glue', 'new_race_launcher'],
                'full_feature_parity': False}
            report['external_dependencies'][profile] = {
                'status': 'REQUIRES ORIGINAL COMPATIBLE HD CLIENT; NOT SELF-CONTAINED',
                'model_closure': 'EXTERNAL BASELINE NOT AVAILABLE; NOT VERIFIED',
                'required_for_integration': ['complete matching HD CreatureModelData.dbc',
                                             'matching HD models, skins, textures and animations'],
                'stock_modeldata_override': False}
            continue
        from build_new_races_assets import validate_closure, validate_compositor
        require(not any(k.split('/')[-1][:-4] in LOCALIZED for k in master if k.endswith('.dbc')),
                'Root Z must not mask locale-owned tables')
        payload = {entry['name'].replace('\\', '/'): entry['data']
                   for package, entries in planned.items() if package.startswith(prefix) and package.count('/') == 2
                   for entry in entries.values()}
        report['new_race_closure'][profile] = validate_closure(payload)
        report['new_race_compositor'][profile] = validate_compositor(payload)
        geometry, eyes = eye_models(payload)
        facial = master['dbfilesclient/characterfacialhairstyles.dbc']['data']
        require(fix_selectors(facial, geometry) == facial, 'High Elf eye selectors are not fixed')
        report.setdefault('high_elf_eyes', {})[profile] = {
            'rows': 22, 'column': 7, 'selector': 2, 'ordinary_geoset': 1702,
            'dk_override': 'UNCHANGED (native class6 selects1703)', 'models': eyes}
        models = rows(master['dbfilesclient/creaturemodeldata.dbc']['data'], 'creaturemodeldata')
        displays = rows(master['dbfilesclient/creaturedisplayinfo.dbc']['data'], 'creaturedisplayinfo')
        missing_models = sorted({r[1] for r in displays.values() if r[1] and r[1] not in models})
        require(not missing_models, f'{profile}: displays reference absent model IDs: {missing_models}')
        report['compatibility'][profile] = 'STRUCTURAL PASS; rendering NOT RUN'
        report['feature_matrix'][profile] = {'principal_native_customizations': 'INCLUDED',
            'new_races_22_23': 'CLIENT ONLY; server integration not included', 'crypt_r5': 'INCLUDED',
            'new_race_glue': 'INCLUDED', 'new_race_launcher': 'INCLUDED', 'unsupported_integrations': []}
        baseline = HD if profile == 'hd_client' else REG
        for key, (_, base) in sources.get(baseline).items():
            if key.endswith('.dbc'):
                diff = record_diff(base, master[key]['data'], key.split('/')[-1][:-4])
                report['dbc_diffs'].setdefault(prefix+'patch-Z.mpq', {}).setdefault(key, {})[baseline] = diff
                require(not diff['removed'] and not diff['changed'], f'Legacy {profile} DBC regression: {key}')
        sections = rows(master['dbfilesclient/charsections.dbc']['data'], 'charsections')
        require(sections == rows(sources.get(NEW)['dbfilesclient/charsections.dbc'][1], 'charsections'), 'Primary skin rows changed')
        # Native custom primary texture references must be physically present, not just DBC rows.
        character_members = planned[prefix+'patch-S.MPQ']
        for row in sections.values():
            for texture in row[4:7]:
                if texture and norm(texture.decode()).startswith('character/custom/'):
                    require(norm(texture.decode()) in character_members, f'Missing primary skin texture: {texture}')
        _, triggers, _ = parse_dbc(master['dbfilesclient/areatrigger.dbc']['data'])
        require([r[1] for r in triggers] == sorted(r[1] for r in triggers), 'AreaTrigger MapID order lost')
        for model, dependencies in lock['native_model_closure'].items():
            raw = character_members[model]['data']
            skins, = struct.unpack_from('<I', raw, 68)
            require(all(model[:-3]+f'{i:02}.skin' in character_members for i in range(skins)), 'Tauren SKIN closure lost')
        en = planned[prefix+'enUS/patch-enUS-Z.MPQ']
        es = planned[prefix+'esES/patch-esES-Z.MPQ']
        require(set(en) == set(es), 'Locale table coverage mismatch')
        for key in en:
            table = key.split('/')[-1][:-4]
            a, b = rows(en[key]['data'], table), rows(es[key]['data'], table)
            require(a.keys() == b.keys(), f'Locale IDs differ: {table}')
            strings = STRINGS.get(table, [])
            mismatches = [(k, i, a[k][i], b[k][i]) for k in a for i in range(len(a[k]))
                          if i not in strings and a[k][i] != b[k][i]]
            if table == 'spell':
                # Both pre-existing complete Spell tables must remain byte-identical. Their
                # legacy ID5 effect multipliers differ, as do localized string flag masks.
                require(all(k == 5 and i in (102, 103, 169, 203) for k, i, _, _ in mismatches),
                        f'Unexpected legacy Spell differences: {mismatches[:10]}')
                report['legacy_spell_locale_differences'] = [list(m) for m in mismatches]
            else:
                require(not mismatches, f'Locale numeric contract differs: {table}: {mismatches[:10]}')
        for locale, expected in (('enUS', b'Northrend'), ('esES', 'Rasganorte'.encode())):
            raw = planned[prefix+locale+'/patch-'+locale+'-Z.MPQ']['dbfilesclient/map.dbc']['data']
            require(expected in rows(raw, 'map')[571][5:21], f'Native Map571 locale lost: {locale}')
            race_bytes = planned[prefix+locale+'/patch-'+locale+'-Z.MPQ']['dbfilesclient/chrraces.dbc']['data']
            races = rows(race_bytes, 'chrraces')
            donor = rows(sources.get(NEW)['dbfilesclient/chrraces.dbc'][1], 'chrraces')
            names = {*range(14, 30), *range(31, 47), *range(48, 64)}
            require(races.keys() == donor.keys() and all(races[k][i] == donor[k][i]
                    for k in donor for i in range(69) if i not in names),
                    f'ChrRaces nonlocalized native contract changed: {locale}')
            native = rows(sources.get('native:'+locale+':dbfilesclient/chrraces.dbc')[
                'dbfilesclient/chrraces.dbc'][1], 'chrraces')
            require(all(races[k][i] == (native[k][i+6] if locale == 'esES' and
                        i in (14, 31, 48) and not native[k][i] else native[k][i])
                        for k in native for i in names),
                    f'ChrRaces native name bank changed: {locale}')
    report['high_elf_eye_opacity'] = {}
    for sex in ('Male', 'Female'):
        key = norm(eye_member(sex))
        source = sources.get(NEW)
        expected, proof = normalize_eye_opacity(source[key][1], source[key[:-3]+'00.skin'][1], sex)
        require(planned['regular_client/Data/patch-S.MPQ'][key]['data'] == expected,
                'Packaged eye opacity differs from validated postprocess')
        report['high_elf_eye_opacity'][sex] = proof
    if hasattr(sources, 'high_elf_native'):
        from package_high_elf_map import audit as map_audit
        report['high_elf_map'] = map_audit(sources.high_elf_native, planned)
        report['feature_matrix']['regular_client']['high_elf_map0'] = 'INCLUDED; offline structural validation only'
    return report


def inventory(planned):
    return {package: {key: {'name': e['name'], 'size': len(e['data']), 'sha256': sha(e['data']),
                           'category': e['category'], 'provenance': e['provenance']}
                      for key, e in sorted(entries.items())} for package, entries in sorted(planned.items())}


def validate_native_delivery(planned, lock):
    """Retain every old delivery hash as an executable pre-extension contract."""
    with tempfile.TemporaryDirectory(prefix='consolidate-native-') as tmp:
        tmp = Path(tmp)
        for package, digest in lock.get('preserved_regular_delivery', {}).items():
            if package.endswith('.exe'):
                require(file_sha(pinned_path('launcher', lock['launcher'])) == digest, 'Native launcher changed')
                continue
            lines = []
            for i, (_, entry) in enumerate(sorted(planned[package].items())):
                disk = tmp / str(i)
                disk.write_bytes(entry['data'])
                lines.append(str(disk)+'|'+entry['name'])
            manifest = tmp/'manifest'
            manifest.write_text('\n'.join(lines)+'\n')
            dest = tmp/'native.MPQ'
            run('create', dest, manifest)
            require(file_sha(dest) == digest, f'Pinned pre-extension delivery changed: {package}')
            dest.unlink()


def build(output, planned, lock, report, native_planned=None):
    require(not output.exists(), f'Build output must be fresh: {output}')
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='consolidate-build-') as tmp:
        tmp = Path(tmp)
        for package, entries in sorted(planned.items()):
            lines = []
            for i, (key, entry) in enumerate(sorted(entries.items())):
                disk = tmp / str(i)
                disk.write_bytes(entry['data'])
                lines.append(str(disk)+'|'+entry['name'])
            manifest = tmp/'manifest'
            manifest.write_text('\n'.join(lines)+'\n')
            dest = output/package
            dest.parent.mkdir(parents=True, exist_ok=True)
            run('create', dest, manifest)
    for profile in lock.get('launcher_profiles', lock['profiles']):
        launcher = pinned_path('launcher', lock['launcher'])
        shutil.copyfile(launcher, output/profile/'Wow-new-races.exe')
    if native_planned is not None:
        validate_native_delivery(native_planned, lock)
    else:
        for path, digest in lock.get('preserved_regular_delivery', {}).items():
            require(file_sha(output/path) == digest, f'Published regular payload changed: {path}')
    dump(output/'inventory.json', inventory(planned))
    dump(output/'validation.json', report)
    sums = {str(p.relative_to(output)): file_sha(p) for p in sorted(output.rglob('*')) if p.is_file()}
    dump(output/'checksums.json', sums)


def verify(output, planned, lock):
    require(json.loads((output/'inventory.json').read_text()) == inventory(planned), 'Inventory differs from source plan')
    expected = set(planned) | {p+'/Wow-new-races.exe' for p in lock.get('launcher_profiles', lock['profiles'])}
    expected |= {'inventory.json', 'validation.json', 'checksums.json'}
    actual = {str(p.relative_to(output)) for profile in lock['profiles'] for p in (output/profile).rglob('*') if p.is_file()}
    actual |= {p for p in ('inventory.json', 'validation.json', 'checksums.json') if (output/p).is_file()}
    require(actual == expected, f'Installation allowlist differs: {actual ^ expected}')
    for package, entries in planned.items():
        require(set(listing(output/package)) == set(entries), f'Unexpected/missing MPQ members: {package}')
        for key, entry in entries.items():
            for name in {entry['name'], key.replace('/', '\\')}:
                require(extract(output/package, name) == entry['data'], f'Readback mismatch: {package}: {name}')
    for profile in lock.get('launcher_profiles', lock['profiles']):
        require(file_sha(output/profile/'Wow-new-races.exe') == lock['launcher']['sha256'], 'Wrong launcher')
    sums = json.loads((output/'checksums.json').read_text())
    require(set(sums) == expected - {'checksums.json'}, 'Checksum coverage differs')
    require(all(file_sha(output/p) == digest for p, digest in sums.items()), 'Delivery hash mismatch')


def publish(output, lock):
    destination = ROOT/'client_patches'
    require(not destination.resolve().is_relative_to(output.resolve()),
            'Publish source must not contain the publication destination')
    # Re-publication may replace only files covered by the previous delivery receipt.
    previous = json.loads((destination/'checksums.json').read_text()) if (destination/'checksums.json').exists() else {}
    for profile in lock['profiles']:
        old = destination/profile
        if old.exists() and any(p.is_dir() for p in old.iterdir()):
            existing = {str(p.relative_to(destination)) for p in old.rglob('*') if p.is_file()}
            expected = {p for p in previous if p.startswith(profile+'/')}
            require(existing == expected and all(file_sha(destination/p) == previous[p] for p in expected),
                    f'Existing profile contains unaccounted/modified files: {profile}')
        else:
            existing = {str(p.relative_to(ROOT)) for p in old.iterdir()} if old.exists() else set()
            require(existing <= set(lock['relocations']), f'Existing profile contains unaccounted files: {profile}')
            require(all(file_sha(ROOT/p) == lock['sources'][p]['sha256'] for p in existing),
                    f'Existing legacy profile contains modified files: {profile}')
    # Stage on the destination filesystem, then retain backups until every swap succeeds.
    transaction = Path(tempfile.mkdtemp(prefix='.consolidate-', dir=destination))
    cleanup = False
    installed = []
    names = [*lock['profiles'], 'inventory.json', 'validation.json', 'checksums.json']
    try:
        staged, backups = transaction/'new', transaction/'previous'
        shutil.copytree(output, staged)
        sums = json.loads((staged/'checksums.json').read_text())
        require(set(sums) == {str(p.relative_to(staged)) for p in staged.rglob('*')
                             if p.is_file() and p != staged/'checksums.json'}, 'Staged receipt coverage differs')
        require(all(file_sha(staged/p) == digest for p, digest in sums.items()), 'Staged delivery hash mismatch')
        backups.mkdir()
        for source, target in lock['relocations'].items():
            if not (ROOT/target).exists():
                (ROOT/target).parent.mkdir(parents=True, exist_ok=True)
                shutil.move(ROOT/source, ROOT/target)
        for name in names:
            target = destination/name
            if target.exists():
                target.rename(backups/name)
            installed.append(name)
            (staged/name).rename(target)
        cleanup = True
    except BaseException:
        for name in reversed(installed):
            target = destination/name
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink(missing_ok=True)
            if (transaction/'previous'/name).exists():
                (transaction/'previous'/name).rename(target)
        cleanup = True
        raise
    finally:
        # If rollback itself fails, leave the backups available for recovery.
        if cleanup:
            shutil.rmtree(transaction)


def archive_optionals():
    """Relocate entire explicitly named incomplete directories, retaining every byte."""
    root = ROOT/'client_patches'
    receipt_path = root/'archive/relocations.json'
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    for relative in ARCHIVE_DIRS:
        source, dest = root/relative, root/'archive'/relative
        require(not source.is_symlink() and not dest.is_symlink(), 'Optional/archive root is a symlink')
        if not source.exists():
            require(str(source.relative_to(ROOT)) in receipt and dest.is_dir(), f'Unrecorded missing optional source: {source}')
            recorded = receipt[str(source.relative_to(ROOT))]
            require(recorded['destination'] == str(dest.relative_to(ROOT)), 'Archived destination differs from receipt')
            require(not any(p.is_symlink() for p in dest.rglob('*')), 'Archived tree contains symlinks')
            sums = {str(p.relative_to(dest)): file_sha(p) for p in sorted(dest.rglob('*')) if p.is_file()}
            require(sums == recorded['files'], f'Archived inventory/hash differs from receipt: {dest}')
            continue
        require(not dest.exists(), f'Archive destination already exists: {dest}')
        require(not any(p.is_symlink() for p in source.rglob('*')), 'Optional tree contains symlinks')
        sums = {str(p.relative_to(source)): file_sha(p) for p in sorted(source.rglob('*')) if p.is_file()}
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, dest)
        require(sums == {str(p.relative_to(dest)): file_sha(p) for p in sorted(dest.rglob('*')) if p.is_file()},
                'Archived bytes changed')
        receipt[str(source.relative_to(ROOT))] = {'destination': str(dest.relative_to(ROOT)), 'files': sums}
        dump(receipt_path, receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--reproducible', action='store_true')
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--archive-optionals', action='store_true')
    parser.add_argument('--native-only', action='store_true',
                        help='Reconstruct the unchanged pinned pre-High-Elf delivery (rollback/research)')
    args = parser.parse_args()
    if args.freeze:
        freeze(args.freeze)
        return
    if args.archive_optionals:
        archive_optionals()
        return
    lock = json.loads(LOCK.read_text())
    sources = Sources(lock)
    planned = plan(lock, sources, include_high_elf=not args.native_only)
    native = getattr(sources, 'high_elf_native', planned)
    report = audit(planned, lock, sources)
    for profile, status in report['compatibility'].items():
        print(f'{profile}: {status}')
    if args.verify:
        validate_native_delivery(native, lock)
        verify(args.verify, planned, lock)
        require(json.loads((args.verify/'validation.json').read_text()) == report, 'Validation report differs')
        print('Verified MPQ readback, member allowlists, provenance, DBC contracts and checksums.')
        if args.publish:
            publish(args.verify, lock)
        return
    require(args.output is not None, '--output or --verify required')
    build(args.output, planned, lock, report, native)
    verify(args.output, planned, lock)
    if args.reproducible:
        with tempfile.TemporaryDirectory(prefix='consolidate-repeat-') as tmp:
            second = Path(tmp)/'delivery'
            build(second, planned, lock, report, native)
            verify(second, planned, lock)
            require({str(p.relative_to(args.output)): file_sha(p) for p in args.output.rglob('*') if p.is_file()} ==
                    {str(p.relative_to(second)): file_sha(p) for p in second.rglob('*') if p.is_file()},
                    'Fresh builds are not byte-identical')
        print('Two fresh builds: all output bytes identical; both independently read back.')
    if args.publish:
        publish(args.output, lock)


if __name__ == '__main__':
    try:
        main()
    except ValueError as error:
        raise SystemExit(str(error)) from None
