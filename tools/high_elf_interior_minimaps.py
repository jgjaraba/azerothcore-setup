#!/usr/bin/env python3
"""Simplified floor cartography, not stock artwork; no world geometry changes.

build_minimaps(assets_dir, native_resolver=None) returns logical TRS keys mapped
to (BLP bytes, JSON-compatible metadata). assets_dir is a staging directory
containing files/ and manifest.json (or its files/ directory). The optional
resolver is a callable(name)->bytes|None; adapt Snapshot with lambda n: s.get(n)[0].
Only missing material textures are requested, never native minimap aliases.

Pure-Python DXT1 uses deterministic RGB565 endpoint quantization (lossy color),
three-color mode and exact binary alpha. No mipmaps or external dependencies.
Projection is U=2*(x-minX), V=H-2*(y-minY); padding remains transparent.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct

from build_crypt_cartography import require, safe_relative
from build_new_races_assets import blp_rgba

PLAN = Path(__file__).with_name('high-elf-interior-minimaps.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def chunks(data):
    result, pos = {}, 0
    while pos < len(data):
        require(pos + 8 <= len(data), 'Truncated WMO chunk')
        tag = data[pos:pos+4][::-1].decode('ascii')
        size = struct.unpack_from('<I', data, pos+4)[0]
        require(pos+8+size <= len(data) and tag not in result, 'Invalid WMO chunk: '+tag)
        result[tag] = data[pos+8:pos+8+size]
        pos += 8+size
    return result


def pinned(data, expected, name):
    require(data is not None, 'Missing resource: '+name)
    require(sha(data) == expected, 'ManifestHash drift: '+name)
    return data


def dimensions(bbox):
    require(len(bbox) == 6 and all(math.isfinite(v) for v in bbox), 'Invalid bbox')
    extents = [(bbox[i+3]-bbox[i])*2 for i in (0, 1)]
    require(all(v > 0 for v in extents), 'Empty bbox')
    return tuple(max(32, min(256, 1 << (math.ceil(v)-1).bit_length())) for v in extents)


def project(vertex, bbox, height):
    return 2*(vertex[0]-bbox[0]), height-2*(vertex[1]-bbox[1])


def triangles(group):
    sub = chunks(group[68:])
    vertices = list(struct.iter_unpack('<3f', sub['MOVT']))
    indices = list(struct.iter_unpack('<3H', sub['MOVI']))
    require(len(sub['MOPY']) == len(indices)*2, 'MOPY/MOVI mismatch')
    for i, ids in enumerate(indices):
        require(max(ids) < len(vertices), 'Invalid MOVI vertex')
        tri = [vertices[j] for j in ids]
        require(all(math.isfinite(x) for v in tri for x in v), 'Nonfinite vertex')
        a, b, c = tri
        ab, ac = [b[j]-a[j] for j in range(3)], [c[j]-a[j] for j in range(3)]
        normal = (ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2],
                  ab[0]*ac[1]-ab[1]*ac[0])
        length = math.sqrt(sum(v*v for v in normal))
        yield tri, normal[2]/length if length else 0, sub['MOPY'][i*2+1]


def raster(group, bbox, colors):
    """Integer subpixel edge coverage; depth from original, unquantized XY plane.

    16-bit fractional texels, pixel centers, inclusive shared edges. Strict depth
    comparison preserves input triangle order on exact ties. No synthetic edges.
    """
    w, h = dimensions(bbox)
    rgba = bytearray(w*h*4)
    zs = [-math.inf]*(w*h)
    selected = Counter()
    scale = 65536
    def edge(a, b, p):
        return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
    for tri, normal, material in triangles(group):
        if normal <= .3 or material not in colors:
            continue
        selected[material] += 1
        uv = [project(v, bbox, h) for v in tri]
        pts = [(round(u*scale), round(v*scale)) for u, v in uv]
        area = edge(pts[0], pts[1], pts[2])
        if not area:
            continue
        sign = 1 if area > 0 else -1
        a, b, c = tri
        den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        for y in range(max(0, math.floor(min(v for u, v in uv))),
                       min(h, math.ceil(max(v for u, v in uv)))):
            for x in range(max(0, math.floor(min(u for u, v in uv))),
                           min(w, math.ceil(max(u for u, v in uv)))):
                p = (x*scale+scale//2, y*scale+scale//2)
                if any(sign*edge(pts[j], pts[(j+1)%3], p) < 0 for j in range(3)):
                    continue
                real_x, real_y = bbox[0]+(x+.5)/2, bbox[1]+(h-y-.5)/2
                s = ((b[1]-c[1])*(real_x-c[0])+(c[0]-b[0])*(real_y-c[1]))/den
                t = ((c[1]-a[1])*(real_x-c[0])+(a[0]-c[0])*(real_y-c[1]))/den
                z = s*a[2]+t*b[2]+(1-s-t)*c[2]
                i = y*w+x
                if z > zs[i]:
                    zs[i] = z
                    rgba[i*4:i*4+4] = bytes((*colors[material], 255))
    return w, h, bytes(rgba), selected


def rgb565(value):
    r, g, b = value >> 11, (value >> 5) & 63, value & 31
    return ((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2))


def encode_dxt1(w, h, rgba):
    require(w % 4 == h % 4 == 0 and len(rgba) == w*h*4, 'Invalid DXT input')
    require(set(rgba[3::4]) <= {0, 255}, 'DXT1 requires binary alpha')
    payload = bytearray()
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            pixels = [rgba[((by+y)*w+bx+x)*4:((by+y)*w+bx+x)*4+4]
                      for y in range(4) for x in range(4)]
            opaque = [p for p in pixels if p[3]]
            quantized = sorted({((p[0]*31+127)//255 << 11) |
                                ((p[1]*63+127)//255 << 5) | ((p[2]*31+127)//255)
                                for p in opaque})
            # Three-color mode always reserves index 3 for transparency.
            lo, hi = (quantized[0], quantized[-1]) if quantized else (0, 0)
            a, b = rgb565(lo), rgb565(hi)
            palette = [a, b, tuple((x+y)//2 for x, y in zip(a, b))]
            bits = 0
            for i, p in enumerate(pixels):
                index = min(range(3), key=lambda k: sum((p[j]-palette[k][j])**2
                            for j in range(3))) if p[3] else 3
                bits |= index << (i*2)
            payload.extend(struct.pack('<HHI', lo, hi, bits))
    header = struct.pack('<4sI4B2I', b'BLP2', 1, 2, 1, 0, 0, w, h)
    return header + struct.pack('<16I', 148, *([0]*15)) + struct.pack(
        '<16I', len(payload), *([0]*15)) + payload


def build_minimaps(assets_dir, native_resolver=None):
    plan = json.loads(PLAN.read_text())
    assets = Path(assets_dir)
    files = assets / 'files' if (assets / 'files').is_dir() else assets
    result, textures = {}, {}
    require(len(plan['groups']) == 11, 'Unapproved group scope')
    for spec in plan['groups']:
        target = 'Character\\Custom\\HighElfMap\\'+spec['file']+'.wmo'
        path = files / safe_relative(target)
        root_raw = pinned(path.read_bytes(), spec['root_sha256'], target)
        root = chunks(root_raw)
        group_path = path.with_name(path.stem+'_001.wmo')
        raw = pinned(group_path.read_bytes(), spec['group_sha256'], str(group_path))
        group = chunks(raw)['MOGP']
        flags = struct.unpack_from('<I', group, 8)[0]
        mogi_flags = struct.unpack_from('<I', root['MOGI'], 32)[0]
        sub = chunks(group[68:])
        require(flags & 0x2000 and mogi_flags & 0x2000 and not flags & 0x1000 and
                'MLIQ' not in sub, 'Unapproved/wet/non-interior group')
        bbox = struct.unpack_from('<6f', group, 12)
        colors, materials = {}, []
        for index, texture_id in spec['materials']:
            tex = plan['textures'][texture_id]
            offset = struct.unpack_from('<I', root['MOMT'], index*64+12)[0]
            name = root['MOTX'][offset:].split(b'\0')[0].decode('ascii')
            require(name.lower() == tex['name'].lower(), 'Material family drift')
            if texture_id not in textures:
                staged = files / safe_relative(name)
                data = staged.read_bytes() if staged.is_file() else (
                    native_resolver(name) if native_resolver else None)
                data = pinned(data, tex['sha256'], name)
                rgba = blp_rgba(data)
                weight = sum(rgba[3::4])
                require(weight > 0, 'Fully transparent floor texture: '+name)
                textures[texture_id] = [sum(rgba[i]*rgba[i-i%4+3]
                    for i in range(c, len(rgba), 4))//weight for c in range(3)]
            colors[index] = textures[texture_id]
            materials.append({'index': index, **tex, 'average_rgb': colors[index]})
        w, h, rgba, counts = raster(group, bbox, colors)
        require(dict(counts) == {i: n for i, n in spec['triangles']}, 'Floor selection drift')
        require(any(rgba[3::4]), 'Empty floor projection')
        blp = encode_dxt1(w, h, rgba)
        digest = sha(blp)
        key = target[6:-4]+'_001_00_00.blp'
        require(key not in result, 'Duplicate logical key')
        result[key] = (blp, {'physical_name': digest[:32]+'.blp', 'sha256': digest,
            'art': 'simplified WMO floor cartography; not stock artwork',
            'encoding': 'BLP2 DXT1 RGB565 lossy color, exact binary alpha, no mipmaps',
            'root_sha256': spec['root_sha256'], 'group_sha256': spec['group_sha256'],
            'family': spec['family'], 'group_index': 1, 'grid': [0, 0],
            'bbox': list(bbox), 'dimensions': [w, h], 'origin': list(bbox[:2]),
            'projection': 'U=2*(x-minX); V=H-2*(y-minY)', 'texel_size': .5,
            'materials': materials, 'selected_triangles': sum(counts.values()),
            'opaque_pixels': sum(a != 0 for a in rgba[3::4])})
    return result


def write_candidate(output, mapping):
    output = Path(output)
    require(not output.exists(), 'Use a fresh output directory')
    output.mkdir(parents=True)
    entries, names = {}, {}
    for key, (data, meta) in mapping.items():
        name = meta['physical_name']
        require(name not in names or names[name] == data, 'Truncated SHA collision')
        names[name] = data
        (output / name).write_bytes(data)
        entries[key] = meta
    report = {'schema': 1, 'plan_sha256': sha(PLAN.read_bytes()), 'tiles': entries}
    (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native', type=Path, help='Optional native Snapshot root')
    args = parser.parse_args()
    snapshot = None
    if args.native:
        from high_elf_map_assets import ROOT, Snapshot
        # Snapshot performs targeted extraction only; no extract-all.
        snapshot = Snapshot(args.native, '335', args.output.parent /
                            (args.output.name+'-inputs'), ROOT/'tools/mpq')
    try:
        mapping = build_minimaps(args.assets, (lambda n: snapshot.get(n)[0]) if snapshot else None)
        report = write_candidate(args.output, mapping)
        print(json.dumps({'tiles': len(mapping), 'plan_sha256': report['plan_sha256'],
                          'output': str(args.output)}, indent=2))
    finally:
        if snapshot:
            snapshot.close()


if __name__ == '__main__':
    main()
