#!/usr/bin/env python3
"""Build an optional Spanish-art edition of r3 without changing map geometry.

Only writes to a new --output directory. Text is read from Turtle's Spanish
DBC strings. Original DXT1 blocks outside the five label regions are retained
byte-for-byte. This is a Spanish edition of the artwork, not locale detection:
the baked labels are Spanish for every client using this optional T archive.
"""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import struct
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from dbc_write import read_dbc_bytes

ROOT = Path(__file__).resolve().parent.parent
R3_SHA = '2532cc09a85b9495637391aaf4ffed2f2d0b44ca857ed3c376ea09fedb5ec35d'
FONT_SHA = '8f798feb09a0e9dc97daf0a54b52a9a1a7b4cf7103fcb2aa1566ab36ac4dc41c'
LABELS = [
    ('title', (357, 32, 671, 65), ['CRIPTA DE KARAZHAN'], 19, 1.0),
    ('walk', (693, 108, 783, 136), ['PASEO DEL', 'INDIGENTE'], 10, 0.2),
    ('slough', (33, 457, 140, 488), ['EL CIENO DE LA', 'DESESPERACIÓN'], 9, 0.0),
    ('sinners', (385, 607, 513, 638), ['LOS PECADORES', 'COLGADOS'], 10, 0.2),
    ('tomb', (830, 602, 958, 636), ['TUMBA DE LOS', 'IMPENITENTES'], 10, 0.2),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(*args):
    return subprocess.run([str(a) for a in args], check=True, capture_output=True).stdout


def string(block, offset):
    end = block.find(b'\0', offset)
    if not 0 <= offset <= end:
        raise ValueError('Invalid DBC string')
    return block[offset:end].decode('utf-8')


def paint_labels(image, font_path):
    original = np.array(image.convert('RGBA'))
    mask = np.zeros(original.shape[:2], dtype=np.uint8)
    for _, (x0, y0, x1, y1), _, _, _ in LABELS:
        mask[y0:y1, x0:x1] = 255
    cleaned = cv2.inpaint(original[:, :, :3], mask, 4, cv2.INPAINT_TELEA)
    rgba = np.dstack((cleaned, original[:, :, 3]))
    base = Image.fromarray(rgba)
    scale = 4
    overlay = Image.new('RGBA', (image.width*scale, image.height*scale))
    draw = ImageDraw.Draw(overlay)
    for key, (x0, y0, x1, y1), lines, size, spacing in LABELS:
        font = ImageFont.truetype(str(font_path), size*scale)
        spacing *= scale
        row_height = (size + 2) * scale
        y = ((y0+y1)*scale - len(lines)*row_height) / 2
        for text in lines:
            widths = [draw.textlength(c, font=font) for c in text]
            width = sum(widths) + spacing*(len(text)-1)
            if width + 4*scale > (x1-x0)*scale:
                raise ValueError(f'Translation exceeds label region: {key}')
            x = ((x0+x1)*scale - width) / 2
            fill = (229, 185, 61, 255) if key == 'title' else (241, 214, 147, 255)
            for c, advance in zip(text, widths):
                draw.text((x, y), c, font=font, fill=fill, anchor='lt',
                          stroke_width=scale//2, stroke_fill=(56, 36, 13, 255))
                x += advance + spacing
            y += row_height
    overlay = overlay.resize(image.size, Image.Resampling.LANCZOS)
    # Confine all editing to explicit regions, including anti-aliasing edges.
    blended = np.array(Image.alpha_composite(base, overlay))
    blended[mask == 0] = original[mask == 0]
    return Image.fromarray(blended), mask


def replace_blocks(original, edited, mask):
    if original[:4] != b'BLP2':
        raise ValueError('Expected BLP2')
    kind, encoding, alpha, alpha_encoding, mips, w, h = struct.unpack_from('<I4B2I', original, 4)
    if (kind, encoding, alpha, alpha_encoding, mips, w, h) != (1, 2, 1, 0, 0, 256, 256):
        raise ValueError('Unexpected world-map BLP format')
    offset = struct.unpack_from('<I', original, 20)[0]
    size = struct.unpack_from('<I', original, 84)[0]
    if size != 32768 or offset + size > len(original):
        raise ValueError('Invalid DXT1 data range')
    output = BytesIO()
    edited.save(output, format='DDS', pixel_format='DXT1')
    dds = output.getvalue()
    if dds[:4] != b'DDS ' or dds[84:88] != b'DXT1' or len(dds) != 128 + size:
        raise ValueError('Unexpected DXT1 encoder output')
    result = bytearray(original)
    count = 0
    for by in range(64):
        for bx in range(64):
            if mask[by*4:by*4+4, bx*4:bx*4+4].any():
                pos = (by*64+bx)*8
                result[offset+pos:offset+pos+8] = dds[128+pos:128+pos+8]
                count += 1
    return bytes(result), count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    out = args.output.resolve()
    if out.exists():
        raise ValueError('Use a fresh output directory')
    base = ROOT / 'work/client-overlay-r3/Data/patch-T.MPQ'
    if sha(base.read_bytes()) != R3_SHA:
        raise ValueError('Unexpected r3 baseline')
    out.mkdir(parents=True)
    source = out / 'source'
    source.mkdir()
    mpq = ROOT / 'tools/mpq'
    sources = {}
    def extract(archive, name, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        run(mpq, 'extract-one', archive, name, dest)
        sources[str(archive) + '|' + name] = sha(dest.read_bytes())
        return dest.read_bytes()
    font_path = source / 'FRIZQT__.TTF'
    font = extract('/home/dev/wow-turtle/Data/fonts.MPQ', r'Fonts\FRIZQT__.TTF', font_path)
    if sha(font) != FONT_SHA:
        raise ValueError('Unexpected source font')
    terms = {}
    for table, fields in [('AreaTable', 25), ('WMOAreaTable', 20)]:
        raw = extract('/home/dev/wow-turtle/Data/patch-9.mpq',
                      f'DBFilesClient\\{table}.dbc', source / (table + '.dbc'))
        fc, rows, strings = read_dbc_bytes(raw)
        if fc != fields:
            raise ValueError('Unexpected source DBC format')
        if table == 'AreaTable':
            terms['title'] = {string(strings, r[17]) for r in rows if r[0] == 5086}
        else:
            for key, group in [('walk', 18701), ('slough', 18812),
                               ('sinners', 18811), ('tomb', 18815)]:
                terms[key] = {string(strings, r[17]) for r in rows
                              if r[1:4] == [3833, 0, group]}
    for key, _, lines, _, _ in LABELS:
        if len(terms[key]) != 1 or ' '.join(lines) != next(iter(terms[key])).upper():
            raise ValueError(f'Translation does not match source: {key}: {terms[key]}')
    entries, files = [], {}
    for line in run(mpq, 'list', base).decode().splitlines():
        name, _ = line.rsplit('\t', 1)
        if name.startswith('('):
            continue
        parts = name.replace('\\', '/').split('/')
        if any(p in ('', '.', '..') or ':' in p for p in parts):
            raise ValueError('Unsafe archive name')
        path = out / 'payload' / Path(*parts)
        extract(base, name, path)
        entries.append((path, name))
        files[name.lower()] = path
    canvas = Image.new('RGBA', (1024, 768))
    tiles = []
    for i in range(1, 13):
        path = files[f'interface\\worldmap\\karazhancrypt\\karazhancrypt{i}.blp']
        image = Image.open(path).convert('RGBA')
        if image.size != (256, 256):
            raise ValueError('Unexpected tile dimensions')
        x, y = (i-1) % 4 * 256, (i-1) // 4 * 256
        canvas.paste(image, (x, y))
        tiles.append((path, x, y, path.read_bytes()))
    canvas.save(out / 'before.png')
    edited, mask = paint_labels(canvas, font_path)
    edited.save(out / 'edited-preview.png')
    final_canvas = Image.new('RGBA', canvas.size)
    changed = []
    for path, x, y, raw in tiles:
        tile_mask = mask[y:y+256, x:x+256]
        result, blocks = replace_blocks(raw, edited.crop((x, y, x+256, y+256)), tile_mask)
        decoded = Image.open(BytesIO(result)).convert('RGBA')
        # Compression may affect only the exact 4x4 blocks intersecting label regions.
        expanded = tile_mask.reshape(64,4,64,4).max(axis=(1,3)).repeat(4,0).repeat(4,1)
        old_pixels = np.array(Image.open(BytesIO(raw)).convert('RGBA'))
        if not np.array_equal(np.array(decoded)[expanded == 0], old_pixels[expanded == 0]):
            raise ValueError('Image changed outside label blocks')
        final_canvas.paste(decoded, (x, y))
        path.write_bytes(result)
        if result != raw:
            changed.append(dict(tile=path.name, changed_blocks=blocks,
                                source_sha256=sha(raw), output_sha256=sha(result)))
    final_canvas.save(out / 'spanish-map.png')
    manifest = out / 'patch.list'
    manifest.write_text(''.join(f'{p}|{n}\n' for p,n in entries))
    final = out / 'Data/patch-T.MPQ'
    final.parent.mkdir()
    run(mpq, 'create', final, manifest)
    check = out / 'roundtrip'
    check.mkdir()
    for i, (path, name) in enumerate(entries):
        dest = check / str(i)
        run(mpq, 'extract-one', final, name, dest)
        if dest.read_bytes() != path.read_bytes():
            raise ValueError(f'MPQ round-trip failed: {name}')
    report = dict(base_sha256=R3_SHA, output_sha256=sha(final.read_bytes()),
                  entries=len(entries), translated_labels={k:next(iter(v)) for k,v in terms.items()},
                  changed_tiles=changed, source_sha256=sources,
                  scope='Optional Spanish baked-art edition; all other r3 content unchanged',
                  in_game_validated=False)
    (out / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'source_sha256'}, indent=2,
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
