#!/usr/bin/env python3
"""Client-only preview candidate. Fresh output; never installs into a client.

Build converter first with scripts/build-new-races-model-converter.sh, then:
 DOTNET=/path/to/dotnet python3 tools/build_new_races_assets.py --output work/FRESH
  --publish copies only owned editions/reports into client_patches/new-races,
  refusing existing destinations. No server data or canonical S is written.
Imaging dependencies: tools/troll-customizations-requirements.txt (pinned).
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

from high_elf_eye_selectors import eye_models, fix_selectors

ROOT = Path(__file__).resolve().parents[1]
MPQ = ROOT / 'tools/mpq'
MANIFEST = ROOT / 'tools/new-races-assets.json'
SCHEMAS = {'ChrRaces': (69, 276), 'CharSections': (10, 40),
           'CharBaseInfo': (2, 2), 'CharStartOutfit': (77, 296),
           'CreatureModelData': (28, 112), 'CreatureDisplayInfo': (16, 64),
           'CharacterFacialHairStyles': (8, 32), 'CharHairGeosets': (6, 24)}
CLASSES = {22: [1, 2, 3, 4, 5, 8], 23: [1, 3, 4, 8, 9]}
MPQ_METADATA = {'(listfile)', '(attributes)'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def run(args):
    p = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    require(p.returncode == 0, f'Command failed: {args}: {p.stderr}')
    return p.stdout


def norm(name):
    name = name.replace('\\', '/')
    require(not name.startswith('/') and all(p not in ('', '.', '..') for p in name.split('/')),
            f'Unsafe archive path: {name}')
    return name


def extract(archive, member):
    with tempfile.TemporaryDirectory(prefix='new-races-') as tmp:
        dest = Path(tmp) / 'member'
        p = subprocess.run([str(MPQ), 'extract-one', str(archive), member, str(dest)],
                           capture_output=True, text=True)
        if p.returncode:
            require('file not found in archive' in p.stderr, f'Archive read failed: {archive}: {p.stderr}')
            return None
        return dest.read_bytes()


def listing(archive):
    names = [line.rsplit('\t', 1)[0] for line in run([MPQ, 'list', archive]).splitlines()]
    require(len({n.lower() for n in names}) == len(names), 'Duplicate archive names')
    require(not any(n.lower().startswith('file000') for n in names), 'Unresolved archive names')
    return names


def ordinary_names(names):
    # Explicit metadata only: '(custom).bin' is an ordinary preserved member.
    require('(signature)' not in {n.lower() for n in names}, 'Signed baseline requires a dedicated signature policy')
    return [n for n in names if n.lower() not in MPQ_METADATA]


class DBC:
    """Append-only WDBC; packed schemas are deliberately explicit."""
    def __init__(self, raw, fields, size):
        require(len(raw) >= 20 and raw[:4] == b'WDBC', 'Invalid DBC magic/header')
        n, f, s, z = struct.unpack_from('<4I', raw, 4)
        require((f, s) == (fields, size), f'Unexpected packed schema: {(f,s)} != {(fields,size)}')
        require(len(raw) == 20 + n*s + z and z > 0, 'Truncated/trailing DBC data')
        self.fields, self.size = f, s
        self.rows = [raw[20+i*s:20+(i+1)*s] for i in range(n)]
        self.strings = raw[20+n*s:]
        require(self.strings[:1] == b'\0' and self.strings[-1:] == b'\0', 'Invalid string block')
        self.original = (list(self.rows), self.strings)

    def values(self):
        fmt = '<BB' if self.size == 2 else '<I4B72i' if self.size == 296 else '<'+'I'*(self.size//4)
        return [list(struct.unpack(fmt, r)) for r in self.rows]

    def text(self, offset):
        require(0 <= offset < len(self.strings), 'String offset outside block')
        return self.strings[offset:self.strings.index(0, offset)].decode('utf-8')

    def string(self, text):
        if not text:
            return 0
        raw = text.encode() + b'\0'
        index = self.strings.find(b'\0' + raw)
        if index >= 0:
            return index + 1
        offset = len(self.strings)
        self.strings += raw
        return offset

    def append(self, rows, key=lambda r: r[0]):
        old = {key(r) for r in self.values()}
        keys = [key(r) for r in rows]
        require(len(set(keys)) == len(keys) and not old.intersection(keys), 'ID/tuple collision')
        fmt = '<BB' if self.size == 2 else '<I4B72i' if self.size == 296 else '<'+'I'*(self.size//4)
        self.rows.extend(struct.pack(fmt, *r) for r in rows)

    def encode(self):
        rows, strings = self.original
        require(self.rows[:len(rows)] == rows and self.strings.startswith(strings), 'Old DBC bytes changed')
        return struct.pack('<4s4I', b'WDBC', len(self.rows), self.fields, self.size, len(self.strings)) + b''.join(self.rows) + self.strings


class Sources:
    def __init__(self, manifest):
        self.m = manifest
        self.cache = {}
        self.verified = {}

    def archive(self, name):
        path = Path(name)
        if not path.is_absolute():
            path = ROOT / path
        if name not in self.verified:
            require(file_sha(path) == self.m['archives'][name], f'Unknown archive: {path}')
            self.verified[name] = self.m['archives'][name]
        return path

    def get(self, key):
        if key not in self.cache:
            spec = self.m['sources'][key]
            raw = extract(self.archive(spec['archive']), spec['member'])
            require(raw is not None and sha(raw) == spec['sha256'], f'Unknown source bytes: {key}')
            self.cache[key] = raw
        return self.cache[key]


def relocate(name):
    p = norm(name).split('/')
    require(len(p) >= 3 and p[0].lower() == 'character' and p[1].lower() in ('bloodelf', 'goblin'),
            f'Unexpected character resource: {name}')
    return '/'.join(['Character', 'Custom', 'TurtleHighElf' if p[1].lower() == 'bloodelf' else 'TurtleGoblin', *p[2:]])


def array(raw, offset, width):
    count, start = struct.unpack_from('<II', raw, offset)
    require(start + count*width <= len(raw), 'Model array out of bounds')
    return [raw[start+i*width:start+(i+1)*width] for i in range(count)]


def texture_names(raw, offset):
    result = []
    for row in array(raw, offset, 16):
        kind, flags, count, start = struct.unpack('<4I', row)
        require(start + count <= len(raw), 'M2 texture name out of bounds')
        result.append((kind, raw[start:start+count].rstrip(b'\0').decode() if count else ''))
    return result


def palette_rgba(raw, level=0):
    """BLP2 palette decoding, including the separate little-endian alpha plane.

    Deliberately no Pillow: the palette's fourth byte is not texel alpha.
    """
    require(raw[:4] == b'BLP2' and raw[8] == 1, 'Expected native BLP2 palette')
    depth = raw[9]
    w, h = struct.unpack_from('<II', raw, 12)
    w, h = max(1, w >> level), max(1, h >> level)
    off = struct.unpack_from('<I', raw, 20+4*level)[0]
    count = w*h
    require(depth in (0, 1, 4, 8) and off >= 1172 and off+count+(count*depth+7)//8 <= len(raw),
            'Invalid palette/alpha plane')
    result = bytearray(count*4)
    for i, index in enumerate(raw[off:off+count]):
        p = 148+4*index
        result[4*i:4*i+3] = raw[p:p+3][::-1]
        if depth:
            packed = raw[off+count+(i*depth)//8]
            alpha = ((packed >> ((i*depth)%8)) & ((1 << depth)-1)) * (255//((1 << depth)-1))
        else:
            alpha = 255
        result[4*i+3] = alpha
    return bytes(result)


def blp_rgba(raw, level=0):
    """Decode native palette or DXT BLP2 top mip without palette-alpha bugs."""
    from build_forest_troll_skins import validate_blp
    info = validate_blp(raw)
    require(info['magic'] == 'BLP2', 'Proof requires BLP2')
    if info['encoding'] == 1:
        return palette_rgba(raw, level)
    require(info['encoding'] == 2, 'Proof requires palette or DXT texture')
    mip = info['mips'][level]
    w, h = mip['width'], mip['height']
    offset = mip['offset']; encoding = info['alpha_encoding']
    result = bytearray(w*h*4)
    for by in range((h+3)//4):
        for bx in range((w+3)//4):
            alpha = [255]*16
            if encoding == 1:
                bits = int.from_bytes(raw[offset:offset+8], 'little'); offset += 8
                alpha = [((bits >> (4*i)) & 15)*17 for i in range(16)]
            elif encoding == 7:
                a, b = raw[offset:offset+2]
                values = [a, b]
                if a > b:
                    values += [((7-i)*a+i*b)//7 for i in range(1, 7)]
                else:
                    values += [((5-i)*a+i*b)//5 for i in range(1, 5)]+[0, 255]
                bits = int.from_bytes(raw[offset+2:offset+8], 'little'); offset += 8
                alpha = [values[(bits >> (3*i)) & 7] for i in range(16)]
            a, b, indices = struct.unpack_from('<HHI', raw, offset); offset += 8
            def rgb565(v):
                r, g, b = v >> 11, (v >> 5) & 63, v & 31
                return ((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2))
            colors = [rgb565(a), rgb565(b)]
            if a > b or encoding != 0:
                colors += [tuple((2*x+y)//3 for x, y in zip(*colors)),
                           tuple((x+2*y)//3 for x, y in zip(*colors))]
            else:
                colors += [tuple((x+y)//2 for x, y in zip(*colors)), (0, 0, 0)]
            for i in range(16):
                x, y = bx*4+i%4, by*4+i//4
                index = (indices >> (2*i)) & 3
                if x < w and y < h:
                    p = (y*w+x)*4
                    result[p:p+4] = bytes((*colors[index], 0 if encoding == 0 and a <= b and index == 3 else alpha[i]))
    return bytes(result)


def compositor_roles(payload):
    """CharSections Texture slots consumed by the native CPU palette accessor."""
    sections = DBC(payload['DBFilesClient/CharSections.dbc'], 10, 40)
    roles = {}
    slots = {0: (0,), 1: (0, 1), 2: (0, 1), 3: (1, 2), 4: (0, 1)}
    for row in sections.values():
        if row[1] not in CLASSES:
            continue
        for slot in slots.get(row[3], ()):
            if row[4+slot]:
                name = norm(sections.text(row[4+slot]))
                roles.setdefault(name, []).append({'row_id': row[0], 'race': row[1],
                    'sex': row[2], 'section': row[3], 'variation': row[8],
                    'color': row[9], 'texture_slot': slot+1})
    return roles


def validate_compositor(payload):
    from build_forest_troll_skins import validate_blp
    folded = {n.lower(): r for n, r in payload.items()}
    roles = compositor_roles(payload)
    for name in roles:
        raw = folded[name.lower()]
        info = validate_blp(raw)
        require(info['magic'] == 'BLP2' and info['encoding'] == 1,
                f'CPU compositor requires palette encoding1: {name}')
    return {'status': 'PASS (all active CPU roles palette1; native runtime NOT RUN)',
            'textures': len(roles), 'roles': roles}


def prepare_compositor(payload, sources):
    from new_races_palette import normalize
    roles = compositor_roles(payload)
    policy = sources.m['cpu_texture_normalization']
    targets = {}
    for prefix, suffixes in policy['source_members'].items():
        for suffix in suffixes:
            member = prefix+suffix+'.blp'
            key = 'texture:'+member.replace('/', '\\').lower()
            targets[relocate(member)] = {'source': key, **sources.m['sources'][key]}
    selected = {n for n in roles if payload[n][8] != 1}
    require(len(targets) == 44 and selected == set(targets), 'CPU normalization allowlist drift')
    records = {}
    for name in sorted(selected):
        spec = targets[name]
        raw = payload[name]
        require(sha(raw) == spec['sha256'] and raw == sources.get(spec['source']),
                'CPU texture source provenance drift')
        require(raw[:4] == b'BLP2' and raw[8] == 2 and raw[10] == 0,
                'Normalization accepts only allowlisted DXT1')
        payload[name], record = normalize(raw)
        records[name] = {**record, 'source': spec, 'roles': roles[name],
                         'runtime_evidence': policy['runtime_evidence']}
    return records


def validate_closure(payload):
    """Only new contributions are checked; no claims about preexisting art."""
    folded = {norm(n).lower(): raw for n, raw in payload.items()}
    require(len(folded) == len(payload), 'Case-folded payload collision')
    dynamic = set()
    sections = DBC(payload['DBFilesClient/CharSections.dbc'], 10, 40)
    for row in sections.values():
        if row[1] not in CLASSES:
            continue
        for offset in row[4:7]:
            if offset:
                path = norm(sections.text(offset))
                require(path.startswith('Character/Custom/Turtle'), 'Texture escapes isolated namespace')
                require(path.lower() in folded, f'Unclosed dynamic texture: {path}')
                dynamic.add(path)
    model_table = DBC(payload['DBFilesClient/CreatureModelData.dbc'], 28, 112)
    model_refs = []
    for row in model_table.values():
        if not 91000 <= row[0] <= 91003:
            continue
        mdx = norm(model_table.text(row[2]))
        require(mdx.endswith('.mdx'), 'Expected DBC MDX spelling')
        m2 = mdx[:-4]+'.m2'
        require(m2.lower() in folded, 'Missing M2 for new MDX reference')
        raw = folded[m2.lower()]
        require(raw[:8] == b'MD20\x08\x01\0\0', 'Unconverted M2')
        for i in range(struct.unpack_from('<I', raw, 68)[0]):
            require((m2[:-3]+f'{i:02}.skin').lower() in folded, 'Unclosed M2 skin')
        for kind, name in texture_names(raw, 80):
            if name:
                require(norm(name).lower() in folded, f'Unclosed named M2 resource: {name}')
                require(norm(name).startswith('Character/Custom/Turtle'), 'M2 texture escapes namespace')
        sequences = array(raw, 28, 64)
        require(all(struct.unpack_from('<I', seq, 12)[0] & 0x100 for seq in sequences), 'External animation dependency')
        model_refs.append(m2)
    require(len(model_refs) == 4, 'Expected all four isolated models')
    return {'status': 'PASS (new active references only)', 'dynamic_blps': sorted(dynamic),
            'mdx_to_m2': model_refs, 'external_animations': 0}


def build_models(sources, output, converter, dotnet):
    from high_elf_eye_opacity import normalize_eye_opacity
    payload, reports, geometry = {}, {}, {}
    for i, spec in enumerate(sources.m['models']):
        raw = sources.get(spec['source'])
        src = output / 'model-inputs' / (str(i)+'.m2')
        src.parent.mkdir(exist_ok=True)
        src.write_bytes(raw)
        target_name = spec['target']
        dest = output / 'models' / target_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        ns = target_name.rsplit('/', 1)[0].replace('/', '\\')
        args = [dotnet, converter, 'convert', '--source', src, '--output', dest, '--namespace', ns]
        for kind, name in texture_names(raw, 92):
            if kind == 0 and name:
                # CLI requires each literal target inside the model's namespace.
                target = ns + '\\Textures\\' + sha(name.lower().encode())[:12] + '.blp'
                args += ['--texture-map', name+'='+target]
        run(args)
        report = json.loads(Path(str(dest)+'.report.json').read_text())
        require(report['sourceSha256'] == sha(raw) and report['embeddedAnimations'] and not report['externalAnimations'],
                'Converter provenance/animation contract failed')
        for entry in report['files']:
            blob = dest.with_name(entry['name']).read_bytes()
            require(sha(blob) == entry['sha256'], 'Converter output checksum mismatch')
            payload[norm(str(Path(target_name).parent / entry['name']))] = blob
        converted = bytearray(dest.read_bytes())
        n, start = struct.unpack_from('<II', converted, 80)
        named_resources = []
        for j, (kind, name) in enumerate(texture_names(converted, 80)):
            if not name:
                continue
            if kind == 0:
                original = next(r['source'] for r in report['hardcodedResources'] if r['textureIndex'] == j)
                target = norm(name)
            else:
                original = name
                target = relocate(name)
                text = target.replace('/', '\\').encode()+b'\0'
                struct.pack_into('<II', converted, start+j*16+8, len(text), len(converted))
                converted.extend(text)
            resource = sources.get('texture:'+original.lower())
            require(target not in payload or payload[target] == resource, 'Texture target collision')
            payload[target] = resource
            named_resources.append({'type': kind, 'source': original, 'target': target, 'sha256': sha(resource)})
        payload[target_name] = bytes(converted)
        require(raw[180:236] == converted[160:216], 'Converted bounds changed')
        require(array(raw, 68, 48) == array(converted, 60, 48), 'Source vertices changed')
        skin = dest.with_name(dest.stem+'00.skin').read_bytes()
        opacity = None
        if spec['race'] == 22:
            packaged, opacity = normalize_eye_opacity(bytes(converted), skin, ('Male', 'Female')[spec['sex']])
            payload[target_name] = packaged
        geosets = [struct.unpack_from('<H', r)[0] for r in array(skin, 28, 48)]
        geometry[(spec['race'], spec['sex'])] = set(geosets)
        reports[str(91000+i)] = {'converter': report, 'named_resources': named_resources,
                                'converter_intermediate_sha256': sha(dest.read_bytes()),
                                'packaged_sha256': sha(payload[target_name]), 'geosets': geosets,
                                'eye_opacity_postprocess': opacity,
                                'name_only_relocation': 'Nonzero replaceable texture names relocated after conversion; numeric texture types unchanged',
                                'bounds': list(struct.unpack_from('<14f', converted, 160))}
    return payload, reports, geometry


def baseline(sources, key, table):
    return DBC(sources.get(key), *SCHEMAS[table])


def require_absent(archive, members):
    """Direct-open every exact member with one read-only archive handle."""
    spellings = [p for name in sorted(members) for p in (name, name.replace('\\', '/'))]
    with tempfile.TemporaryDirectory(prefix='new-races-native-probe-') as temp:
        root = Path(temp)
        request = root/'request.txt'
        request.write_text('\n'.join(spellings)+'\n')
        destination = root/'extracted'; destination.mkdir()
        proc = subprocess.run([str(MPQ), 'extract-list', str(archive), str(request), str(destination)],
                              capture_output=True, text=True)
        expected = ['WARN: not found '+name for name in spellings]+['# extracted 0 files']
        require(proc.returncode == 0 and proc.stderr.splitlines() == expected and not list(destination.rglob('*')),
                f'Native placeholder exists or direct probes failed; revisit repair policy: {archive}: {proc.stderr}')


def verify_legacy_hair(sources):
    """Prove source choices match native no-scalp controls before clearing slots.

    The supplied native snapshot does NOT contain these scalp assets either.
    Do not confuse identical declared names with actual available resources.
    """
    source = DBC(sources.get('source:CharSections'), 10, 40)
    native = DBC(sources.get('validation:NativeCharSections'), 10, 40)
    require(len(native.rows) == 8958, 'Unexpected native appearance proof baseline')
    src_geo = DBC(sources.get('source:CharHairGeosets'), 6, 24)
    nat_geo = DBC(sources.get('native:CharHairGeosets'), 6, 24)
    choices = lambda t: {r[3]: r[4:] for r in t.values() if r[1:3] == [10, 1]}
    expected = {s: [s+2, 0] for s in range(20)}
    require(choices(src_geo) == choices(nat_geo) == expected,
            'Source/native female hair no-scalp controls differ')
    rows = [r for r in source.values() if r[1:4] == [10, 1, 3] and r[9] == 0]
    require(len(rows) == 320 and {(r[4], r[5]) for r in rows} ==
            {(s, c) for s in range(20) for c in range(16)}, 'Incomplete source female hair bank')
    native_rows = [r for r in native.values() if r[1:4] == [10, 1, 3]]
    comparisons = []
    for color in range(11):
        name = rf'Character\BloodElf\Hair00_{color:02}.blp'
        src = sources.get('texture:'+name.lower())
        nat = sources.get('validation:NativeHair:'+str(color))
        a, b = blp_rgba(src), blp_rgba(nat)
        require(len(a) == len(b), 'Hair proof dimension mismatch')
        differences = [abs(x-y) for x, y in zip(a, b)]
        comparisons.append({'color': color, 'source_sha256': sha(src), 'native_sha256': sha(nat),
                            'source_rgba_sha256': sha(a), 'native_rgba_sha256': sha(b),
                            'byte_exact': src == nat, 'rgba_exact': a == b,
                            'rgba_mean_absolute_error': sum(differences)/len(differences),
                            'rgba_max_absolute_error': max(differences),
                            'disposition': 'Comparison only; all packaged hair bytes remain original Turtle. No native art substitution.'})
    declared = []
    for row in rows:
        style, color = row[4:6]
        refs = [source.text(o) for o in row[6:9]]
        require(refs[0].lower() == rf'character\bloodelf\hair00_{color:02}.blp', 'Unexpected source female hair texture')
        fallback = min(color, 10)
        expected_refs = [rf'Character\BloodElf\ScalpLowerHair00_{fallback:02}.blp',
                         rf'Character\BloodElf\ScalpUpperHair00_{fallback:02}.blp']
        require(refs[1:] == expected_refs, 'Unexpected source scalp fallback')
        require(any([native.text(o) for o in r[5:7]] == expected_refs for r in native_rows),
                'Scalp declarations do not match exact native full paths')
        declared.append({'style': style, 'color': color, 'source_hair': refs[0],
                         'source_scalp_declarations': refs[1:], 'declared_scalp_color': fallback,
                         'show_scalp': 0, 'output_scalp_slots': [0, 0]})
    facial_paths = {native.text(o).lower() for r in native.values() if r[1:4] == [10, 0, 2] for o in r[4:6]}
    missing = {name for name in sources.m['missing'] if 'scalp' in name or 'facial' in name}
    require(len(missing) == 42 and all(name in facial_paths for name in missing if 'facial' in name),
            'Legacy facial paths differ from native counterparts')
    for archive_name in sources.m['native_legacy_probe_archives']:
        archive = sources.archive(archive_name)
        require_absent(archive, missing)
    return {'status': 'PASS static no-scalp compatibility proof; runtime NOT RUN',
            'source_rows_restored': 320, 'matching_native_hair_choices': 20,
            'geosets': list(range(2, 22)), 'all_show_scalp': 0,
            'native_absent_paths': sorted(missing), 'native_probe_archives': sources.m['native_legacy_probe_archives'],
            'native_scalp_assets_reused': 0, 'generated_or_recolored_scalp_assets': 0,
            'hair_comparisons': comparisons, 'source_declared_choices': declared,
            'policy': 'Preserve all original source hair Texture1 and geometry. Clear only unused scalp overlay slots under matching native ShowScalp=0 controls; no actual native scalp exists in this snapshot.'}


def build_tables(sources, edition, models, geometry):
    tables = {t: baseline(sources, edition+':'+t if t in ('CharSections', 'CharacterFacialHairStyles') else 'native:'+t, t)
              for t in SCHEMAS}
    counts = {t: len(d.rows) for t, d in tables.items()}
    require(counts['CharBaseInfo'] == 72 and counts['ChrRaces'] == 21 and counts['CreatureDisplayInfo'] == 24263,
            'Unexpected project baseline counts')
    require(counts['CharSections'] == (9302 if edition == 'primary' else 9452) and counts['CharacterFacialHairStyles'] == 233,
            'Stale customization edition')
    t = tables['ChrRaces']; lookup = {r[0]: r for r in t.values()}
    source_classes = DBC(sources.get('source:CharBaseInfo'), 2, 2)
    require(len(source_classes.rows) == 59, 'Unknown source class revision')
    for source_race, target in ((10, 22), (9, 23)):
        require(sorted(r[1] for r in source_classes.values() if r[0] == source_race) == CLASSES[target],
                'Source classes differ from pinned contract')
    for spec in sources.m['races']:
        row = lookup[spec['clone_native_chr_races_id']].copy()
        for k, v in spec['numeric_overrides'].items():
            row[int(k)] = v
        for k, v in spec['string_overrides'].items():
            row[int(k)] = t.string(v)
        for col in (20, 37, 54):  # locale index6 = esES in each 16-string bank
            row[col] = t.string('Alto Elfo' if row[0] == 22 else 'Goblin')
        t.append([row])
    tables['CharBaseInfo'].append([[r, c] for r, classes in CLASSES.items() for c in classes], key=tuple)
    require(len(tables['CharBaseInfo'].rows) == 83, 'Class combination count')
    require(len(set(tables['CharBaseInfo'].rows)) == 83, 'Duplicate class tuples')
    for table, donors in [('CreatureDisplayInfo', [15476, 15475, 6894, 6895]),
                          ('CreatureModelData', [2208, 2209, 831, 832])]:
        t = tables[table]; rows = {r[0]: r for r in t.values()}
        for i, donor in enumerate(donors):
            row = rows[donor].copy(); row[0] = 91000+i
            if table == 'CreatureDisplayInfo':
                row[1], row[3] = 91000+i, 0
            else:
                # Preserve donor flags and every other unknown field. These bits
                # are not an established NPC-only mask (playable donors use them).
                row[2] = t.string(sources.m['models'][i]['target'].replace('/', '\\')[:-3]+'.mdx')
                # DBC fields17..22 are the model bounding box. Converter preserves the
                # classic actual bounding-box header (M2 v264 offset160) byte-for-byte.
                bounds = models[str(91000+i)]['bounds']
                row[17:23] = list(struct.unpack('<6I', struct.pack('<6f', *bounds[:6])))
                row[4] = 0x3f800000
                require(all(row[c] == rows[donor][c] for c in range(28)
                            if c not in (0, 2, 4, 17, 18, 19, 20, 21, 22)),
                        'ModelData clone changed donor flags or unknown fields')
            t.append([row])
    t = tables['CharStartOutfit']; rows = {r[0]: r for r in t.values()}
    added = []
    for i, spec in enumerate(sources.m['outfits']):
        row = rows[spec['clone_native_outfit_id']].copy()
        require(row[2:4] == [spec['target_class'], spec['sex']], 'Outfit donor class/sex mismatch')
        require(row[5:29] == spec['items'] and row[29:53] == spec['displays'], 'Outfit donor changed')
        row[0], row[1] = 90000+i, spec['target_race']
        added.append(row)
    require(len(added) == 22 and len({tuple(r[1:5]) for r in added}) == 22, 'Outfit tuple collision')
    t.append(added)
    items = DBC(sources.get('validation:Item'), 8, 32)
    item_ids = {r[0] for r in items.values()}
    display_raw = sources.get('validation:ItemDisplayInfo')
    _, f, s, _ = struct.unpack_from('<4I', display_raw, 4)
    display_ids = {r[0] for r in DBC(display_raw, f, s).values()}
    require(all(x <= 0 or x in item_ids for r in added for x in r[5:29]), 'Missing outfit item')
    require(all(x <= 0 or x in display_ids for r in added for x in r[29:53]), 'Missing outfit display')
    src = DBC(sources.get('source:CharSections'), 10, 40)
    t = tables['CharSections']; added = []; textures = {}; cleanup = []; excluded = []; deferred = []
    for row in src.values():
        if row[1] not in (9, 10):
            continue
        if row[9] != 0:
            excluded.append(row[0]); continue
        refs = []
        for slot, offset in enumerate(row[6:9]):
            name = src.text(offset)
            if name and name.lower() in sources.m['missing']:
                policy = sources.m['missing'][name.lower()]
                require((row[1], row[3], slot) in ((10, 2, 0), (10, 2, 1), (10, 3, 1), (10, 3, 2), (10, 4, 1)),
                        'Missing texture outside explicit cleanup slots')
                cleanup.append({'source_row': row[0], 'slot': slot, 'source': name, 'policy': policy})
                name = ''
            if name:
                target = relocate(name)
                textures[target] = sources.get('texture:'+name.lower())
                refs.append(t.string(target.replace('/', '\\')))
            else:
                refs.append(0)
        added.append([22000+len(added), 22 if row[1] == 10 else 23, *row[2:4], *refs,
                      1 if row[3] == 1 else 17, row[4], row[5]])
    keys = lambda r: tuple(r[i] for i in (1, 2, 3, 8, 9))
    require(len({keys(r) for r in added}) == len(added), 'Customization tuple collision')
    # IDs stay assigned in original source order; only appended physical rows move.
    added.sort(key=keys)
    t.append(added)
    final_keys = [keys(r) for r in t.values()]
    require(final_keys == sorted(final_keys), 'CharSections must be fully ordered by Race/Sex/Base/Variation/Color')
    # Assert the complete ordinary skin/face Cartesian banks, not manufactured aliases.
    for race, skins, faces in [(22, 11, [10, 10]), (23, 3, [4, 6])]:
        for sex in (0, 1):
            actual = {(r[8], r[9]) for r in added if r[1:4] == [race, sex, 1]}
            require(actual == {(f, c) for f in range(faces[sex]) for c in range(skins)}, 'Incomplete face bank')
            require({r[9] for r in added if r[1:4] == [race, sex, 0]} == set(range(skins)), 'Incomplete body bank')
            hair = {(r[8], r[9]) for r in added if r[1:4] == [race, sex, 3]}
            expected_hair = {(h, c) for h in range(([16, 20] if race == 22 else [14, 17])[sex])
                             for c in range(16 if race == 22 else 5)}
            require(hair == expected_hair, 'Incomplete hair bank')
    for table, fields, size in [('CharHairGeosets', 6, 24), ('CharacterFacialHairStyles', 9, 36)]:
        src = DBC(sources.get('source:'+table), fields, size)
        added_rows = []
        for row in src.values():
            race = row[1] if table == 'CharHairGeosets' else row[0]
            if race not in (9, 10):
                continue
            target = 22 if race == 10 else 23
            if table == 'CharHairGeosets':
                new = [22000+len(added_rows), target, *row[2:]]
                require(row[5] or row[4] in geometry[(target, row[2])], 'Missing hair geoset')
            else:
                new = [target, *row[1:3], *row[6:9], 0, 0]
                # Client facial channels are group100, group300, group200,
                # respectively (not monotonically numbered group IDs).
                for group, number in zip((1, 3, 2), row[6:9]):
                    require(not number or 100*group+number in geometry[(target, row[1])],
                            f'Missing facial geoset: {target}/{row[1]} group{group} value{number}')
            added_rows.append(new)
        added_rows.sort(key=(lambda r: tuple(r[:3])) if table == 'CharacterFacialHairStyles'
                        else (lambda r: tuple(r[1:4])))
        tables[table].append(added_rows, key=(lambda r: tuple(r[:3])) if table == 'CharacterFacialHairStyles' else (lambda r: r[0]))
    payload = {'DBFilesClient/'+name+'.dbc': t.encode() for name, t in tables.items()}
    facial = 'DBFilesClient/CharacterFacialHairStyles.dbc'
    payload[facial] = fix_selectors(payload[facial], geometry)
    report = {name: {'old_rows': counts[name], 'new_rows': len(t.rows)-counts[name], 'total_rows': len(t.rows),
                     'old_rows_byte_exact': True, 'old_string_prefix_byte_exact': True,
                     'sha256': sha(payload['DBFilesClient/'+name+'.dbc'])} for name, t in tables.items()}
    return payload, textures, {'tables': report, 'cleanup': cleanup, 'deferred_cosmetic_rows': deferred,
                               'charsections_full_natural_key_order': True,
                               'new_customization_rows_sorted_only': True,
                               'model_donor_flags': {str(91000+i): {'donor': donor,
                                   'flags': next(r[1] for r in tables['CreatureModelData'].values() if r[0] == donor)}
                                   for i, donor in enumerate((2208, 2209, 831, 832))},
                               'excluded_paid_npc_source_rows': excluded,
                               'outfit_ids': [r[0] for r in added_outfits(tables['CharStartOutfit'])]}


def added_outfits(table):
    return [r for r in table.values() if r[1] in CLASSES]


def package(sources, base_key, payload, destination, staging):
    base = sources.archive(sources.m['baselines'][base_key])
    names = listing(base)
    before = {norm(n).lower(): (norm(n), extract(base, n)) for n in ordinary_names(names)}
    require(len(before) == len(ordinary_names(names)), 'Archive collision')
    combined = {name: raw for name, raw in before.values()}
    by_lower = {name.lower(): name for name in combined}
    for name, raw in payload.items():
        if name.lower() in by_lower:
            del combined[by_lower[name.lower()]]
        combined[name] = raw
    staging.mkdir(parents=True, exist_ok=False)
    lines = []
    for i, (name, raw) in enumerate(sorted(combined.items(), key=lambda x: x[0].lower())):
        disk = staging / str(i)
        disk.write_bytes(raw)
        # mpq create preserves insertion order; normalize filetimes below.
        os.utime(disk, (0, 0))
        lines.append(str(disk)+'|'+name.replace('/', '\\'))
    entries = staging / 'entries.txt'; entries.write_text('\n'.join(lines)+'\n')
    destination.parent.mkdir(parents=True, exist_ok=True)
    run([MPQ, 'create', destination, entries])
    after_names = ordinary_names(listing(destination))
    require({norm(n).lower() for n in after_names} == {n.lower() for n in combined}, 'MPQ inventory mismatch')
    for name, raw in combined.items():
        require(extract(destination, name.replace('/', '\\')) == raw, f'MPQ readback mismatch: {name}')
    changed = {n.lower() for n in payload}
    preserved = {name: sha(raw) for low, (name, raw) in before.items() if low not in changed}
    return {'baseline': str(base), 'baseline_sha256': file_sha(base), 'sha256': file_sha(destination),
            'members': len(combined), 'unrelated_members_preserved': preserved,
            'payload': {n: {'sha256': sha(r), 'bytes': len(r)} for n, r in sorted(payload.items())}}


def build(output, converter, dotnet, publish=False):
    output = output.resolve()
    require(output.is_relative_to(ROOT / 'work') and not output.exists(), 'Output must be fresh under work/')
    m = json.loads(MANIFEST.read_text()); sources = Sources(m)
    require(converter.resolve() == (ROOT/'work/toolchains/new-races-model-converter/NewRacesModelConverter.dll').resolve()
            or file_sha(converter) == file_sha(ROOT/'work/toolchains/new-races-model-converter/NewRacesModelConverter.dll'),
            'Custom converter must match the validated build')
    env = os.environ.copy(); env['DOTNET'] = dotnet
    proc = subprocess.run([str(ROOT/'scripts/build-new-races-model-converter.sh'), '--validate'],
                          env=env, capture_output=True, text=True)
    require(proc.returncode == 0, 'Converter validation failed: '+proc.stderr)
    output.mkdir(parents=True)
    legacy_hair = verify_legacy_hair(sources)
    model_payload, models, geometry = build_models(sources, output, converter, dotnet)
    _, eyes = eye_models(model_payload)
    from build_new_races_glue import build as build_glue
    build_glue(output/'glue')
    glue = {str(p.relative_to(output/'glue/payload')): p.read_bytes() for p in (output/'glue/payload').rglob('*') if p.is_file()}
    report = {'status': 'CLIENT-ONLY PREVIEW CANDIDATE; NOT SERVER-CREATABLE', 'runtime': 'NOT RUN',
              'classes': CLASSES, 'class_pairs': 83, 'models': models,
              'semantic_gates': m['semantic_gates'], 'legacy_hair_proof': legacy_hair,
              'high_elf_eyes': eyes, 'editions': {}}
    from build_forest_troll_skins import validate_blp
    blps = {}
    for edition in ('primary', 'optional-extra-skins'):
        tables, textures, table_report = build_tables(sources, edition, models, geometry)
        payload = {**model_payload, **textures, **glue, **tables}
        normalizations = prepare_compositor(payload, sources)
        table_report['cpu_compositor'] = validate_compositor(payload)
        table_report['resource_closure'] = validate_closure(payload)
        for name, raw in payload.items():
            if name.lower().endswith('.blp'):
                if name not in blps:
                    info = validate_blp(raw)
                    if info['magic'] == 'BLP2' and info['encoding'] == 1:
                        rgba = palette_rgba(raw)
                        info['top_rgba_sha256'] = sha(rgba)
                        info['alpha_min'], info['alpha_max'] = min(rgba[3::4]), max(rgba[3::4])
                        info['decoder'] = 'project separate-alpha-plane; palette fourth byte ignored'
                    info['preserved_source_bytes'] = name not in normalizations
                    if name in normalizations:
                        info['formatNormalizations'] = normalizations[name]
                    blps[name] = info
        archives = {}
        for base_key, relative in [('root', 'Data/patch-Z.mpq'), ('locale', 'Data/esES/patch-esES-Z.MPQ')]:
            dest = output/edition/relative
            archives[relative] = package(sources, base_key, payload, dest, output/'mpq-staging'/edition/base_key)
        report['editions'][edition] = {**table_report, 'archives': archives}
    report['blp_metadata'] = blps
    report['source_archives'] = sources.verified
    report['source_resources'] = m['sources']
    report['glue'] = json.loads((output/'glue/report.json').read_text())
    tool_paths = ['tools/build_new_races_assets.py', 'tools/build_new_races_glue.py',
                  'tools/new_races_palette.py', 'tools/high_elf_eye_selectors.py',
                  'tools/high_elf_eye_opacity.py',
                  'tools/troll-customizations-requirements.txt',
                  'tools/test_new_races_palette.py', 'tools/new-races-assets.json',
                  'tools/patch_new_races_client.py', 'tools/test_new_races_assets.py',
                  'work/toolchains/new-races-model-converter/build-manifest.json']
    report['build_tools_sha256'] = {p: file_sha(ROOT/p) for p in tool_paths}
    report['model_toolchain'] = {'validated': True, 'converter_sha256': file_sha(converter),
                                'build_manifest': json.loads((ROOT/tool_paths[-1]).read_text())}
    dump(output/'report.json', report)
    files = [p for e in ('primary', 'optional-extra-skins') for p in sorted((output/e).rglob('*')) if p.is_file()]
    (output/'SHA256SUMS').write_text(''.join(file_sha(p)+'  '+str(p.relative_to(output))+'\n' for p in files))
    if publish:
        publish_output(output)
    return report


def publication_path(name):
    """Resolve logical edition names without changing historical report keys."""
    base = 'client_patches/archive/new-races' if name.split('/', 1)[0] == 'optional-extra-skins' else 'client_patches/new-races'
    return ROOT/base/name


def publish_output(output, validation=None, replace_known=False):
    dest = ROOT/'client_patches/new-races'
    def confined(name):
        target = publication_path(name)
        base = ROOT/'client_patches/archive/new-races' if name.split('/', 1)[0] == 'optional-extra-skins' else dest
        require(target.resolve().is_relative_to(base.resolve()), 'Publication path escapes destination')
        for part in (target, *target.parents):
            require(not part.is_symlink(), 'Symlink publication path')
            if part == ROOT:
                break
        return target
    names = ['primary', 'optional-extra-skins', 'assets-report.json', 'assets-SHA256SUMS']
    if validation is not None:
        names.append('assets-validation.json')
        evidence = json.loads(validation.read_text())
        require(evidence['status'] == 'PASS' and evidence['source_builds'] == 2, 'Invalid validation report')
        expected_archives = {f'{edition}/{relative}' for edition in ('primary', 'optional-extra-skins')
                             for relative in ('Data/patch-Z.mpq', 'Data/esES/patch-esES-Z.MPQ')}
        require(set(evidence['archives']) == expected_archives, 'Validation must cover exactly all four publication archives')
        for relative, digest in evidence['archives'].items():
            require(file_sha(output/relative) == digest, 'Validated artifacts differ from publication inputs')
        report = json.loads((output/'report.json').read_text())
        for relative, digest in evidence['archives'].items():
            edition, member = relative.split('/', 1)
            require(report['editions'][edition]['archives'][member]['sha256'] == digest,
                    'Report archives differ from validated artifacts')
    owned = [f'{edition}/{relative}' for edition in names[:2]
             for relative in ('Data/patch-Z.mpq', 'Data/esES/patch-esES-Z.MPQ')]
    owned += names[2:]
    for name in owned:
        confined(name)
    previous = None
    if replace_known:
        require(validation is not None, 'Known upgrade requires two-build validation')
        previous = json.loads(MANIFEST.read_text())['previous_publication']
        require(all(confined(n).is_file() and not confined(n).is_symlink() and file_sha(confined(n)) == digest
                    for n, digest in previous.items()), 'Unknown current publication; refusing upgrade')
        checksums = {line.split('  ', 1)[1]: line.split('  ', 1)[0]
                     for line in (dest/'assets-SHA256SUMS').read_text().splitlines()}
        require(checksums == previous, 'Unknown current publication checksum list')
        backup = output/'replaced-publication'
        require(not backup.exists(), 'Publication backup must be fresh')
        backup.mkdir()
        for name in [*previous, 'assets-SHA256SUMS']:
            target = backup/name; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(confined(name), target)
    else:
        require(all(not confined(n).exists() for n in names), 'Publication destination already exists')
    dest.mkdir(parents=True, exist_ok=True)
    new_files = {f'{edition}/{relative}': output/edition/relative for edition in names[:2]
                 for relative in ('Data/patch-Z.mpq', 'Data/esES/patch-esES-Z.MPQ')}
    new_files['assets-report.json'] = output/'report.json'
    if validation is not None:
        new_files['assets-validation.json'] = validation
    # Stage every file before replacing any; replacement is limited to explicitly
    # owned, hash-checked paths. Parent-owned EXE/docs or other files are retained.
    with tempfile.TemporaryDirectory(prefix='publication-', dir=output) as temp:
        staging = Path(temp)
        for name, source in new_files.items():
            target = staging/name; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        checksums = ''.join(file_sha(staging/name)+'  '+name+'\n' for name in new_files)
        (staging/'assets-SHA256SUMS').write_text(checksums)
        replacements = [*new_files, 'assets-SHA256SUMS']
        originals = {name: confined(name).read_bytes() if confined(name).exists() else None
                     for name in replacements}
        completed = []
        created_dirs = set()
        try:
            for name in replacements:
                target = confined(name)
                parent = target.parent
                while not parent.exists():
                    created_dirs.add(parent)
                    parent = parent.parent
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(staging/name, target)
                completed.append(name)
        except Exception:
            for name in reversed(completed):
                target = confined(name)
                if originals[name] is None:
                    target.unlink()
                else:
                    target.write_bytes(originals[name])
            for directory in sorted(created_dirs, key=lambda p: len(p.parts), reverse=True):
                directory.rmdir()
            raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--model-converter', type=Path, default=ROOT/'work/toolchains/new-races-model-converter/NewRacesModelConverter.dll')
    p.add_argument('--publish', action='store_true')
    args = p.parse_args()
    report = build(args.output, args.model_converter, os.environ.get('DOTNET', 'dotnet'), args.publish)
    print(json.dumps({'status': report['status'], 'output': str(args.output), 'class_pairs': report['class_pairs']}))


if __name__ == '__main__':
    main()
