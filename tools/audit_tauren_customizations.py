#!/usr/bin/env python3
"""Read-only Tauren research from existing inventory; verifies extracted DBC pins.

No client or server writes. Output must be a fresh project work/ directory.
Archive precedence is only the audit's static approximation, not loader proof.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct
import subprocess

import numpy as np
from PIL import Image, ImageDraw

import audit_turtle_skins as base
import build_troll_customizations as codec

ROOT = base.ROOT


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inventory', type=Path, default=ROOT / 'work/turtle-skins-audit-verified')
    p.add_argument('--output', type=Path, default=ROOT / 'work/tauren-customization-audit')
    args = p.parse_args()
    out = args.output.resolve()
    if out.exists() or not out.is_relative_to((ROOT / 'work').resolve()):
        p.error('Choose a fresh output below work/')
    datasets = json.loads((args.inventory / 'dbc-audit.json').read_text())
    out.mkdir(parents=True)
    result = {}
    for client in ('turtle', '335'):
        root = Path('/home/dev/wow-turtle/Data' if client == 'turtle' else '/home/dev/wow-335/Data')
        index = defaultdict(list)
        for listing in sorted(args.inventory.glob(client + '__*.listing.tsv')):
            archive = root / listing.name[len(client) + 2:-len('.listing.tsv')].replace('__', '/')
            for line in listing.read_text().splitlines():
                if '\t' not in line:
                    continue
                name, size = line.rsplit('\t', 1)
                index[name.replace('/', '\\').lower()].append(dict(archive=str(archive), member=name, size=int(size)))
        for entries in index.values():
            entries.sort(key=lambda entry: base.priority(Path(entry['archive'])), reverse=True)
        folder = out / client
        folder.mkdir()
        data = result[client] = dict(tables={}, resources={})
        def extract(entry, path):
            subprocess.run([str(base.MPQ), 'extract-one', entry['archive'],
                            entry.get('member', entry.get('name')), str(path)], check=True, capture_output=True)
            return path.read_bytes()
        for table in ('CharSections', 'CharHairGeosets', 'CharacterFacialHairStyles'):
            entry = datasets[client][table]['candidates_priority_approx'][0]
            path = folder / (table + '.dbc')
            raw = extract(entry, path)
            assert hashlib.sha256(raw).hexdigest() == entry['sha256']
            header, rows, text = base.dbc(path)
            if table == 'CharSections':
                rows = [base.section(client, row, text) for row in rows]
                rows = [row for row in rows if row['race'] == 6]
            else:
                rows = [row for row in rows if row[1 if table == 'CharHairGeosets' else 0] == 6]
            data['tables'][table] = dict(source=entry, header=header, rows=rows)
        referenced = defaultdict(list)
        for row in data['tables']['CharSections']['rows']:
            for name in row['textures']:
                if name:
                    referenced[name.lower()].append(row['id'])
        names = set(referenced) | {name for name in index if name.startswith('character\\tauren\\')}
        names |= {name for name in index if 'tauren' in name and 'shop' in name and name.endswith('.blp')}
        batches = defaultdict(list)
        for name in sorted(names):
            if index.get(name):
                batches[index[name][0]['archive']].append(name)
        for number, (archive, batch) in enumerate(batches.items()):
            destination = folder / f'batch-{number}'
            destination.mkdir()
            request = folder / f'request-{number}.txt'
            request.write_text(''.join(index[name][0]['member'] + '\n' for name in batch))
            subprocess.run([str(base.MPQ), 'extract-list', archive, str(request), str(destination)],
                           check=True, capture_output=True)
            for name in batch:
                member = index[name][0]['member']
                path = destination / member
                if not path.exists():
                    path = destination / member.replace('\\', '/')
                path.rename(folder / name.replace('\\', '__'))
        for name in sorted(names):
            entries = index.get(name, [])
            meta = data['resources'][name] = dict(candidates=entries, row_ids=referenced.get(name, []))
            if not entries:
                continue
            path = folder / name.replace('\\', '__')
            raw = path.read_bytes()
            meta.update(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            if raw[:4] in (b'BLP1', b'BLP2'):
                try:
                    rgba = codec.decode_blp(raw)
                    meta.update(dimensions=[rgba.shape[1], rgba.shape[0]],
                                rgba_sha256=hashlib.sha256(rgba.tobytes()).hexdigest())
                except ValueError as ex:
                    meta['decode_error'] = str(ex)
        models = {}
        for sex in ('male', 'female'):
            name = f'character\\tauren\\{sex}\\tauren{sex}.m2'
            meta = data['resources'][name]
            raw = (ROOT / meta['path']).read_bytes()
            version, = struct.unpack_from('<I', raw, 4)
            model = models[sex] = dict(version=version, sha256=meta['sha256'], views=[])
            if version == 256:
                count, offset = struct.unpack_from('<2I', raw, 76)
                for view in range(count):
                    n, off = struct.unpack_from('<2I', raw, offset + 44 * view + 24)
                    model['views'].append(sorted({struct.unpack_from('<I', raw, off + 32 * i)[0] for i in range(n)}))
            else:
                count, = struct.unpack_from('<I', raw, 68)
                for view in range(count):
                    skin = name[:-3] + f'{view:02}.skin'
                    sr = (ROOT / data['resources'][skin]['path']).read_bytes()
                    n, off = struct.unpack_from('<2I', sr, 28)
                    model['views'].append(sorted({struct.unpack_from('<H', sr, off + 48 * i)[0] for i in range(n)}))
        data['models'] = models
        for sex, label in ((0, 'male'), (1, 'female')):
            bodies = [row for row in data['tables']['CharSections']['rows'] if row['sex'] == sex and row['base'] == 0]
            image = Image.new('RGB', (5 * 260, ((len(bodies) + 4) // 5) * 286), (40, 40, 40))
            draw = ImageDraw.Draw(image)
            for i, row in enumerate(bodies):
                meta = data['resources'][row['textures'][0].lower()]
                rgba = codec.decode_blp((ROOT / meta['path']).read_bytes())
                thumb = Image.fromarray(rgba).resize((256, 256), Image.Resampling.NEAREST)
                x, y = i % 5 * 260, i // 5 * 286
                image.paste(thumb, (x, y))
                draw.text((x, y + 257), f'id{row["id"]} c{row["color"]} f{row["flags"]}', fill='white')
                draw.text((x, y + 271), row['textures'][0].split('\\')[-1], fill='white')
            image.save(out / f'{client}-{label}-bodies.png')
    (out / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({client: dict(models=data['models'], resources=len(data['resources']),
                                 missing=[k for k, v in data['resources'].items() if not v['candidates']])
                      for client, data in result.items()}, indent=2))


if __name__ == '__main__':
    main()
