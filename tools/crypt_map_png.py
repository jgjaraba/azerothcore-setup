#!/usr/bin/env python3
"""Export the two map editions or reimport a manually edited RGBA PNG.

Uses the pinned dependencies in crypt-map-localization-requirements.txt.
No client/runtime installation is performed. Output directories must be new.
"""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import struct
import subprocess

import numpy as np
from PIL import Image, ImageDraw

from localize_crypt_map import LABELS, replace_blocks

ROOT = Path(__file__).resolve().parent.parent
EN = ROOT / 'work/client-overlay-r3/Data/patch-T.MPQ'
ES = ROOT / 'work/client-overlay-r3-esES-final/Data/patch-T.MPQ'
EN_SHA = '2532cc09a85b9495637391aaf4ffed2f2d0b44ca857ed3c376ea09fedb5ec35d'
ES_SHA = '13ca6b6eb430eff93edb62840d267594b35f2c49e9d2dd47994fbe0cf1cd9233'
PREFIX = 'Interface\\WorldMap\\KarazhanCrypt\\KarazhanCrypt'
MPQ = ROOT / 'tools/mpq'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(*args):
    return subprocess.run([str(a) for a in args], check=True, capture_output=True).stdout


def fresh(path):
    if path.exists():
        raise ValueError('Use a fresh output directory; existing work is preserved')
    path.mkdir(parents=True)


def verify_archive(path, expected):
    if sha(path.read_bytes()) != expected:
        raise ValueError(f'Unexpected archive: {path}')


def assemble(archive, directory):
    directory.mkdir(parents=True)
    canvas = Image.new('RGBA', (1024, 768))
    for i in range(1, 13):
        path = directory / f'{i}.blp'
        run(MPQ, 'extract-one', archive, f'{PREFIX}{i}.blp', path)
        tile = decode_map_blp(path.read_bytes())
        if tile.size != (256, 256):
            raise ValueError('Unexpected source tile dimensions')
        canvas.paste(tile, ((i-1) % 4 * 256, (i-1) // 4 * 256))
    return canvas


def export(out):
    verify_archive(EN, EN_SHA)
    verify_archive(ES, ES_SHA)
    fresh(out)
    for edition, archive in [('original-en', EN), ('actual-es', ES)]:
        image = assemble(archive, out / 'source' / edition)
        image.save(out / (edition + '.png'))
        # Lossless export, including the original transparent padding.
        with Image.open(out / (edition + '.png')) as opened:
            if opened.convert('RGBA').tobytes() != image.tobytes():
                raise ValueError('PNG export was not lossless')
    guide = Image.new('RGBA', (1024, 768))
    draw = ImageDraw.Draw(guide)
    for key, (x0, y0, x1, y1), _, _, _ in LABELS:
        draw.rectangle((x0, y0, x1-1, y1-1), outline=(255, 0, 0, 220), width=1)
    guide.save(out / 'guia-rotulos.png')
    report = dict(canvas=[1024, 768], mode='RGBA', tile_size=[256, 256],
                  tile_order='4 columns x 3 rows, row-major',
                  source_mpq_sha256=dict(english=EN_SHA, spanish=ES_SHA),
                  png_sha256={p.name:sha(p.read_bytes()) for p in out.glob('*.png')},
                  labels={key:' '.join(lines) for key, _, lines, _, _ in LABELS})
    (out / 'manifest.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(report, indent=2, ensure_ascii=False))


def palette_blp2(image):
    """Classic-compatible palette + exact alpha; avoids DXT1 lettering blocks.

    Color quantization is lossy, using 256 colors per edited tile.
    """
    indexed = image.convert('RGB').quantize(colors=255, method=Image.Quantize.MEDIANCUT,
                                          dither=Image.Dither.NONE)
    colors = indexed.getpalette()
    colors = colors + [0] * (768 - len(colors))
    # Reserve index 255 for transparent pixels. The palette's fourth byte is
    # unused by the client; matching alpha there also makes legacy preview
    # decoders that ignore the separate alpha plane display this binary-alpha
    # map correctly. The authoritative alpha is the per-pixel plane below.
    palette = bytes(c for i in range(255)
                    for c in (colors[i*3+2], colors[i*3+1], colors[i*3], 255)) + b'\0'*4
    alpha = image.getchannel('A').tobytes()
    if any(a not in (0, 255) for a in alpha):
        raise ValueError('Expected binary original map alpha')
    indices = bytes(255 if a == 0 else index for index, a in zip(indexed.tobytes(), alpha))
    pixels = indices + alpha
    return (b'BLP2' + struct.pack('<I4B2I', 1, 1, 8, 8, 0, *image.size)
            + struct.pack('<16I', 1172, *([0]*15))
            + struct.pack('<16I', len(pixels), *([0]*15)) + palette + pixels)


def decode_map_blp(data):
    """Decode palette BLP2's separate alpha plane (not supported by Pillow)."""
    if data[:4] == b'BLP2' and data[8] == 1:
        kind, encoding, alpha, alpha_type, mips, w, h = struct.unpack_from('<I4B2I', data, 4)
        offset = struct.unpack_from('<I', data, 20)[0]
        size = struct.unpack_from('<I', data, 84)[0]
        if (kind, encoding, alpha, alpha_type, mips, w, h, offset, size) != (
                1, 1, 8, 8, 0, 256, 256, 1172, 131072) or len(data) != offset+size:
            raise ValueError('Unexpected palette map encoding')
        palette = np.frombuffer(data[148:1172], dtype='uint8').reshape(256, 4)
        indices = np.frombuffer(data[offset:offset+w*h], dtype='uint8')
        rgba = palette[indices][:, [2, 1, 0, 3]].copy()
        rgba[:, 3] = np.frombuffer(data[offset+w*h:], dtype='uint8')
        return Image.fromarray(rgba.reshape(h, w, 4))
    with Image.open(BytesIO(data)) as image:
        return image.convert('RGBA')


def import_png(image_path, out, palette=False):
    verify_archive(EN, EN_SHA)
    with Image.open(image_path) as opened:
        if opened.format != 'PNG' or opened.mode != 'RGBA' or opened.size != (1024, 768):
            raise ValueError('Expected a 1024x768 RGBA PNG with original transparency')
        image = opened.copy()
    fresh(out)
    source = assemble(EN, out / 'source')
    old, new = np.array(source), np.array(image)
    if not np.array_equal(old[:, :, 3], new[:, :, 3]):
        raise ValueError('Alpha/transparency changed; preserve the original map outline')
    # Ignore invisible RGB differences introduced by editors in transparent pixels.
    mask = ((old[:, :, :3] != new[:, :, :3]).any(axis=2) & (old[:, :, 3] > 0)).astype('uint8') * 255
    entries, changed = [], []
    for line in run(MPQ, 'list', EN).decode().splitlines():
        name, _ = line.rsplit('\t', 1)
        if name.startswith('('):
            continue
        parts = name.replace('\\', '/').split('/')
        if any(p in ('', '.', '..') or ':' in p for p in parts):
            raise ValueError('Unsafe archive path')
        path = out / 'payload' / Path(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        run(MPQ, 'extract-one', EN, name, path)
        if name.startswith(PREFIX) and name.endswith('.blp'):
            i = int(name[len(PREFIX):-4])
            if not 1 <= i <= 12:
                raise ValueError('Unexpected world-map tile')
            x, y = (i-1) % 4 * 256, (i-1) // 4 * 256
            tile_mask = mask[y:y+256, x:x+256]
            if tile_mask.any():
                raw = path.read_bytes()
                edited_tile = image.crop((x, y, x+256, y+256))
                if palette:
                    result = palette_blp2(edited_tile)
                    blocks = None
                else:
                    result, blocks = replace_blocks(raw, edited_tile, tile_mask)
                before = np.array(decode_map_blp(raw))
                after = np.array(decode_map_blp(result))
                expanded = tile_mask.reshape(64,4,64,4).max(axis=(1,3)).repeat(4,0).repeat(4,1)
                if not np.array_equal(before[:, :, 3], after[:, :, 3]):
                    raise ValueError('Compression changed map transparency')
                if not palette and not np.array_equal(before[expanded == 0], after[expanded == 0]):
                    raise ValueError('Compression changed unedited blocks')
                path.write_bytes(result)
                changed.append(dict(tile=name, blocks=blocks))
        entries.append((path, name))
    manifest = out / 'patch.list'
    manifest.write_text(''.join(f'{p}|{n}\n' for p,n in entries))
    archive = out / 'Data/patch-T.MPQ'
    archive.parent.mkdir()
    if changed:
        run(MPQ, 'create', archive, manifest)
    else:
        shutil.copyfile(EN, archive)
    check = out / 'roundtrip'
    check.mkdir()
    for i, (path, name) in enumerate(entries):
        result = check / str(i)
        run(MPQ, 'extract-one', archive, name, result)
        if result.read_bytes() != path.read_bytes():
            raise ValueError(f'MPQ integrity mismatch: {name}')
    preview = assemble(archive, out / 'decoded')
    preview.save(out / 'resultado.png')
    report = dict(input_png_sha256=sha(image_path.read_bytes()),
                  output_mpq_sha256=sha(archive.read_bytes()), changed_tiles=changed,
                  edited_blp_encoding='BLP2 palette256 + alpha8' if palette else 'BLP2 DXT1',
                  in_game_validated=False)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=['export', 'import'])
    ap.add_argument('--image', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--palette', action='store_true', help='Use palette256 BLP2 to avoid DXT1 lettering artifacts')
    args = ap.parse_args()
    if args.action == 'export':
        export(args.output.resolve())
    else:
        if not args.image:
            ap.error('--image is required for import')
        import_png(args.image.resolve(), args.output.resolve(), args.palette)
