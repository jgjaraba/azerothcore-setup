#!/usr/bin/env python3
"""Read-only client resource audit; writes only beneath work/turtle-skins-audit.

Priority is an explicit research approximation, never a certified client loader.
Archives are opened by tools/mpq with MPQ_OPEN_READ_ONLY.
"""
import concurrent.futures
import argparse
import hashlib
import json
import pathlib
import struct
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'work/turtle-skins-audit'
MPQ = ROOT / 'tools/mpq'
TABLES = ['CharSections', 'CharHairGeosets', 'CharacterFacialHairStyles',
          'ChrRaces', 'CreatureDisplayInfo', 'CreatureDisplayInfoExtra', 'CreatureModelData']

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(8*1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def priority(p):
    n = p.stem.lower()
    if n.startswith('patch-'):
        return (3, n[6:])
    if n == 'patch':
        return (2, '')
    return (1, n)

def dbc(path):
    b = path.read_bytes()
    magic, n, fields, size, strings = struct.unpack_from('<4s4I', b)
    assert magic == b'WDBC' and size == fields*4 and len(b) == 20+n*size+strings
    s = b[20+n*size:]
    rows = [list(struct.unpack_from('<'+'I'*fields, b, 20+i*size)) for i in range(n)]
    def text(off):
        if off >= len(s):
            raise ValueError('String offset outside DBC string block')
        end = s.find(b'\0', off)
        if end < 0:
            raise ValueError('Unterminated DBC string')
        return s[off:end].decode('utf8', errors='replace')
    return {'records': n, 'fields': fields, 'record_size': size, 'string_size': strings}, rows, text

def section(kind, row, text):
    """Decode source layout only; flags/indices are not converted for deployment."""
    if len(row) != 10 or kind not in ('turtle', '335'):
        raise ValueError('Unsupported CharSections schema')
    if kind == 'turtle':
        ident, race, sex, base, var, color, t1, t2, t3, flags = row
    else:
        ident, race, sex, base, t1, t2, t3, flags, var, color = row
    return dict(id=ident, race=race, sex=sex, base=base, variation=var,
                color=color, flags=flags, textures=[text(t) for t in (t1, t2, t3)])

def texture_dimensions(raw):
    # BLP1 compression/flags and BLP2 type/encoding fields both precede
    # width/height at offsets 12/16 (BLP2 does include a uint32 type field).
    if raw[:4] in (b'BLP1', b'BLP2'):
        return struct.unpack_from('<2I', raw, 12)
    raise ValueError('Not a BLP texture')

def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=pathlib.Path, default=OUT,
                        help='Fresh directory under project work/; never reuse cached audit output')
    args = parser.parse_args()
    OUT = args.output.resolve()
    if not OUT.is_relative_to((ROOT / 'work').resolve()) or OUT == (ROOT / 'work').resolve():
        parser.error('Output must be a new subdirectory of project work/')
    if OUT.exists():
        parser.error('Output already exists; choose a fresh directory to avoid stale listings/resources')
    OUT.mkdir(parents=True)
    inventory, indexes = [], {}
    clients = {'turtle': pathlib.Path('/home/dev/wow-turtle/Data'),
               '335': pathlib.Path('/home/dev/wow-335/Data')}
    for kind, root in clients.items():
        archives = sorted((p for p in root.rglob('*') if p.suffix.lower() == '.mpq'), key=priority, reverse=True)
        index = {}
        for p in archives:
            tag = kind + '__' + str(p.relative_to(root)).replace('/', '__')
            listing = OUT / (tag + '.listing.tsv')
            if not listing.exists():
                r = subprocess.run([str(MPQ), 'list', str(p)], capture_output=True)
                listing.write_bytes(r.stdout)
                if r.returncode:
                    raise RuntimeError((str(p), r.stderr.decode()))
            entries = []
            for line in listing.read_text(errors='replace').splitlines():
                if '\t' not in line:
                    continue
                name, size = line.rsplit('\t', 1)
                entry = {'archive': str(p), 'name': name, 'size': int(size)}
                index.setdefault(name.lower().replace('/', '\\'), []).append(entry)
                entries.append(entry)
            st = p.stat()
            inventory.append({'kind': kind, 'path': str(p), 'size': st.st_size,
                              'mtime_ns': st.st_mtime_ns, 'listed_files': len(entries)})
        indexes[kind] = index
    # Hash complete archives concurrently, not just their file listings.
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        hashes = pool.map(lambda e: sha(pathlib.Path(e['path'])), inventory)
        for e, h in zip(inventory, hashes):
            e['sha256'] = h
    (OUT/'archives.json').write_text(json.dumps(inventory, indent=2))
    datasets = {}
    for kind, index in indexes.items():
        target = OUT/kind
        target.mkdir(exist_ok=True)
        datasets[kind] = {}
        for table in TABLES:
            key = 'dbfilesclient\\'+table.lower()+'.dbc'
            copies = index.get(key, [])
            result = {'candidates_priority_approx': copies}
            for i, e in enumerate(copies):
                dest = target/(table+f'.{i}.dbc')
                subprocess.run([str(MPQ), 'extract-one', e['archive'], e['name'], str(dest)], check=True, capture_output=True)
                e['sha256'] = sha(dest)
                e['extracted'] = str(dest.relative_to(OUT))
            if copies:
                header, rows, text = dbc(OUT/copies[0]['extracted'])
                result['header'] = header
                if table == 'CharSections':
                    parsed = []
                    for r in rows:
                        decoded = section(kind, r, text)
                        textures = decoded['textures']
                        presence = []
                        for name in textures:
                            k = name.lower().replace('/', '\\')
                            presence.append({c: ix.get(k, []) for c,ix in indexes.items()} if name else {})
                        parsed.append(dict(decoded, presence=presence))
                    result['rows'] = parsed
                else:
                    result['rows'] = rows
                    # Keep all valid strings with offsets for schema-independent investigation.
                    b = (OUT/copies[0]['extracted']).read_bytes()[20+header['records']*header['record_size']:]
                    strings, pos = {}, 0
                    while pos < len(b):
                        end = b.find(b'\0', pos)
                        if end < 0: break
                        if end > pos: strings[pos] = b[pos:end].decode('utf8', errors='replace')
                        pos = end+1
                    result['strings'] = strings
            datasets[kind][table] = result
        # Full filename inventory remains useful for assets not referenced by CharSections.
        needles = ('forest', 'darktroll', 'felorc', 'leper', 'darkiron', 'wildhammer',
                   'manari', 'maghar', 'skeleton', 'charactercreate', 'dressup', 'shop', 'donat')
        matches = {k:v for k,v in index.items() if any(n in k for n in needles)}
        (target/'named-families.json').write_text(json.dumps(matches, indent=2))
        for key, copies in matches.items():
            if key.endswith('.lua') and ('charactercreate' in key or 'turtle_shopui' in key or 'turtle_barbershop' in key):
                e = copies[0]
                subprocess.run([str(MPQ), 'extract-one', e['archive'], e['name'], str(target/key.rsplit('\\',1)[-1])], check=True, capture_output=True)
    (OUT/'dbc-audit.json').write_text(json.dumps(datasets, indent=2))
    resources = {}
    for kind, data in datasets.items():
        index = indexes[kind]
        names = {t.lower().replace('/', '\\') for r in data['CharSections']['rows'] if r['base'] == 0 for t in r['textures'] if t}
        names |= {k for k in index if k.startswith('character\\') and k.endswith('.m2') and k.count('\\') == 3}
        resources[kind] = {}
        target = OUT/kind/'resources'
        target.mkdir(exist_ok=True)
        groups = {}
        for name in sorted(names):
            copies = index.get(name, [])
            if copies:
                e = copies[0]
                dest = target/name.replace('\\','__')
                rawdest = target/e['name']
                if not dest.exists() and not rawdest.exists():
                    groups.setdefault(e['archive'],[]).append(e['name'])
        for num, (archive, group) in enumerate(groups.items()):
            requests = target/f'requests-{num}.txt'
            requests.write_text('\n'.join(group)+'\n')
            subprocess.run([str(MPQ),'extract-list',archive,str(requests),str(target)],check=True,capture_output=True)
        for name in sorted(names):
            copies = index.get(name, [])
            if not copies: continue
            e = copies[0]
            dest = target/name.replace('\\','__')
            if not dest.exists():
                dest = target/e['name']
            b = dest.read_bytes()
            info = {'source': e, 'sha256': sha(dest), 'bytes':len(b)}
            if b[:4] in (b'BLP1', b'BLP2'):
                info.update(magic=b[:4].decode(), dimensions=texture_dimensions(b))
            if b[:4] == b'MD20':
                info.update(magic='MD20', version=struct.unpack_from('<I',b,4)[0], header_uints=list(struct.unpack_from('<24I',b,0)))
            resources[kind][name] = info
    (OUT/'resources.json').write_text(json.dumps(resources, indent=2))
    lines = ['# Measured skin catalog', '', 'Priority is approximate. Flags below are literal source values, not cross-version selectable guarantees.', '',
             '|Race|Sex|Turtle skin flag0 / flag1|Turtle face rows / variants|335 normal skin / DK / NPC|335 normal face rows / variants|',
             '|---|---|---|---|---|---|']
    details = []
    for race in range(1,12):
        for sex in (0,1):
            t = [r for r in datasets['turtle']['CharSections']['rows'] if r['race']==race and r['sex']==sex]
            w = [r for r in datasets['335']['CharSections']['rows'] if r['race']==race and r['sex']==sex]
            ts = [r for r in t if r['base']==0]
            tf = [r for r in t if r['base']==1]
            ws = [r for r in w if r['base']==0]
            wf = [r for r in w if r['base']==1 and r['flags']&1 and not r['flags']&4]
            lines.append(f'|{race}|{sex}|{sum(r["flags"]==0 for r in ts)} / {sum(r["flags"]==1 for r in ts)}|{len(tf)} / {len(set(r["variation"] for r in tf))}|{sum(bool(r["flags"]&1) and not r["flags"]&4 for r in ws)} / {sum(bool(r["flags"]&4) for r in ws)} / {sum(r["flags"]==8 for r in ws)}|{len(wf)} / {len(set(r["variation"] for r in wf))}|')
            for r in ts:
                same = [a for a in ws if a['textures'][0].lower()==r['textures'][0].lower()]
                key=r['textures'][0].lower()
                tr = resources['turtle'].get(key)
                wr = resources['335'].get(key)
                details.append({'race':race,'sex':sex,'turtle':r,'335_same_texture_rows':same,
                                'texture_hash_equal': tr['sha256']==wr['sha256'] if tr and wr else None,
                                '335_same_path_present':bool(wr) or bool(r['presence'][0].get('335'))})
    (OUT/'catalog.md').write_text('\n'.join(lines)+'\n')
    (OUT/'skin-deltas.json').write_text(json.dumps(details,indent=2))
    lines = ['# Source rows needing explicit mapping', '',
             'Source flag 1 is NOT established as Vanilla player-selectable. It overlaps flag-0 color indexes.', '',
             '|Race|Sex|Row ID|Color|Flags|Texture1|335 same-path skin rows (color:flags)|',
             '|---|---|---|---|---|---|---|']
    for a in details:
        r=a['turtle']
        ordinary = any(b['flags']&1 and not b['flags']&4 for b in a['335_same_texture_rows'])
        if r['flags']==0 and ordinary: continue
        refs=', '.join(f'{b["id"]} ({b["color"]}:0x{b["flags"]:x})' for b in a['335_same_texture_rows'])
        lines.append(f'|{r["race"]}|{r["sex"]}|{r["id"]}|{r["color"]}|{r["flags"]}|{r["textures"][0]}|{refs}|')
    (OUT/'extra-source-rows.md').write_text('\n'.join(lines)+'\n')
    # Compare UVs only on shared position+normal vertices; not a visual validation.
    uv_results = []
    def vertex_map(kind, name):
        meta = resources[kind][name]
        folder = OUT/kind/'resources'
        path = folder/name.replace('\\','__')
        if not path.exists(): path = folder/meta['source']['name']
        b = path.read_bytes()
        count, offset = struct.unpack_from('<2I', b, 68 if meta['version']==256 else 60)
        assert offset+count*48 <= len(b)
        vertices = {}
        for i in range(count):
            pos = struct.unpack_from('<3f',b,offset+i*48)
            normal = struct.unpack_from('<3f',b,offset+i*48+20)
            uv = struct.unpack_from('<2f',b,offset+i*48+32)
            key = tuple(round(x,4) for x in pos+normal)
            vertices.setdefault(key,set()).add(tuple(round(x,5) for x in uv))
        return count,vertices
    for name, meta in resources['turtle'].items():
        if 'version' not in meta or name not in resources['335']: continue
        tc,tv = vertex_map('turtle',name)
        wc,wv = vertex_map('335',name)
        shared = tv.keys() & wv.keys()
        equal = sum(tv[k]==wv[k] for k in shared)
        uv_results.append(dict(name=name,turtle_vertices=tc,w335_vertices=wc,
                               shared_position_normal_keys=len(shared),same_uv_sets=equal))
    (OUT/'model-uv-comparison.json').write_text(json.dumps(uv_results,indent=2))
    shops = []
    t = datasets['turtle']
    model_rows = {r[0]:r for r in t['CreatureModelData']['rows']}
    for row in t['CreatureDisplayInfoExtra']['rows']:
        bake = t['CreatureDisplayInfoExtra']['strings'].get(row[18],'')
        if 'shop' not in bake.lower() or bake.lower()=='bishop.blp': continue
        displays = []
        for display in t['CreatureDisplayInfo']['rows']:
            if display[3] != row[0]: continue
            model = model_rows.get(display[1])
            modelname = t['CreatureModelData']['strings'].get(model[2],'') if model else ''
            displays.append({'display_id':display[0],'model_id':display[1],'model_path':modelname})
        path = 'textures\\bakednpctextures\\'+bake.lower()
        shops.append({'extra_row':row,'bake':bake,'displays':displays,
                      'presence':{k:ix.get(path,[]) for k,ix in indexes.items()}})
    (OUT/'shop-baked-catalog.json').write_text(json.dumps(shops,indent=2))
    (OUT/'priority-warning.txt').write_text('Static approximate priority: patch suffix descending, patch, base names descending. Locale enUS/esES treated as candidates, not certified simultaneously loaded. Listings can omit unlisted names. Reference snapshots are not the playing client.\n')
    print(OUT)

if __name__ == '__main__':
    main()
