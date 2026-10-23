#!/usr/bin/env python3
"""Reproducible patch-S v2 from pinned original MPQs, never research inputs.

Use the Python environment pinned by troll-customizations-requirements.txt.
--output must be fresh. --publish backs up accepted v1 and publishes only the
client MPQ/report/checksums, new SQL pair and compact seven-row server DBC.
Does not install into clients, write DEV databases or touch core/source DBCs.
"""
import argparse
import io
import json
import os
from pathlib import Path
import shutil
import struct
import tempfile

import numpy as np
from PIL import Image

import build_forest_troll_skins as forest

ROOT = forest.ROOT
MANIFEST = ROOT / 'tools/troll-customizations.json'
require, digest, sha = forest.require, forest.digest, forest.sha


def validate_blp(raw):
    try:
        return forest.validate_blp(raw)
    except ValueError:
        # Some pinned Turtle facial BLPs have an exporter EOF sentinel in the
        # absent terminal tiny mip: offset=EOF, size=uint32(-EOF). Validate every
        # actual mip strictly; preserve original bytes and report the defect.
        require(raw[:4] == b'BLP2' and raw[8:10] == bytes((1, 8)), 'Invalid source BLP')
        w, h = struct.unpack_from('<2I', raw, 12)
        offsets = struct.unpack_from('<16I', raw, 20)
        sizes = struct.unpack_from('<16I', raw, 84)
        candidates = [i for i in range(16) if offsets[i] == len(raw)
                      and sizes[i] == ((-len(raw)) & 0xffffffff)
                      and max(1, w >> i) <= 2 and max(1, h >> i) == 1]
        require(len(candidates) == 1 and candidates[0] > 0, 'Unrecognized malformed BLP tail')
        i = candidates[0]
        require(not any(offsets[i + 1:]) and not any(sizes[i + 1:15])
                and sizes[15] in (0, sizes[0]), 'Unexpected BLP tail')
        fixed = bytearray(raw)
        struct.pack_into('<I', fixed, 20 + 4 * i, 0)
        struct.pack_into('<I', fixed, 84 + 4 * i, 0)
        struct.pack_into('<I', fixed, 84 + 4 * 15, 0)
        info = forest.validate_blp(bytes(fixed))
        info['source_missing_terminal_mip'] = dict(level=i, offset=offsets[i], size=sizes[i],
                                                   unused_slot15_size=sizes[15],
                                                   preserved_byte_exact=True)
        return info


def decode_blp(raw, level=0):
    """Palette alpha is a separate plane, NOT the unused palette alpha byte."""
    info = validate_blp(raw)
    require(0 <= level < len(info['mips']), 'Missing mip')
    mip = info['mips'][level]
    w, h, off = mip['width'], mip['height'], mip['offset']
    n = w * h
    if raw[:4] == b'BLP2' and info['encoding'] == 1:
        palette = np.frombuffer(raw, np.uint8, 1024, 148).reshape(256, 4)
        indices = np.frombuffer(raw, np.uint8, n, off)
        rgb = palette[indices][:, [2, 1, 0]]
        depth = info['alpha_bits']
        if depth == 0:
            alpha = np.full(n, 255, np.uint8)
        elif depth == 8:
            alpha = np.frombuffer(raw, np.uint8, n, off + n)
        else:
            packed = np.frombuffer(raw, np.uint8, (n * depth + 7) // 8, off + n)
            i = np.arange(n)
            alpha = ((packed[i // (8 // depth)] >> ((i % (8 // depth)) * depth))
                     & ((1 << depth) - 1)) * (255 // ((1 << depth) - 1))
        return np.column_stack((rgb, alpha)).reshape(h, w, 4).astype(np.uint8)
    if raw[:4] == b'BLP2' and info['encoding'] == 3:
        return np.frombuffer(raw, np.uint8, n * 4, off).reshape(h, w, 4)[:, :, [2, 1, 0, 3]].copy()
    require(level == 0, 'Pillow fallback only supports top mip')
    return np.asarray(Image.open(io.BytesIO(raw)).convert('RGBA')).copy()


def encode_blp(rgba):
    """Native BLP2 encoding3 BGRA; deterministic integer box-filter mip chain."""
    require(rgba.dtype == np.uint8 and rgba.ndim == 3 and rgba.shape[2] == 4,
            'Expected uint8 RGBA')
    h, w = rgba.shape[:2]
    require(w & (w - 1) == 0 and h & (h - 1) == 0 and 0 < w <= 8192 and 0 < h <= 8192,
            'Expected power-of-two texture')
    offsets, sizes, chunks = [0] * 16, [0] * 16, []
    current, off = rgba, 148
    for i in range(16):
        chunk = current[:, :, [2, 1, 0, 3]].tobytes()
        offsets[i], sizes[i] = off, len(chunk)
        chunks.append(chunk)
        off += len(chunk)
        y, x = current.shape[:2]
        if x == y == 1:
            break
        # Collapsed dimension repeats its single sample, as a clamped box filter.
        yy = np.minimum(np.arange(max(1, y // 2)) * 2, y - 1)
        xx = np.minimum(np.arange(max(1, x // 2)) * 2, x - 1)
        a = current.astype(np.uint16)
        current = ((a[yy[:, None], xx] + a[np.minimum(yy + 1, y - 1)[:, None], xx]
                    + a[yy[:, None], np.minimum(xx + 1, x - 1)]
                    + a[np.minimum(yy + 1, y - 1)[:, None], np.minimum(xx + 1, x - 1)]
                    + 2) // 4).astype(np.uint8)
    return (struct.pack('<4sI4B2I', b'BLP2', 1, 3, 8, 0, 1, w, h)
            + struct.pack('<16I', *offsets) + struct.pack('<16I', *sizes) + b''.join(chunks))


def prepare_texture(raw, allow_repair=False):
    info = validate_blp(raw)
    metadata = dict(source_original_sha256=digest(raw), byte_exact=True)
    if 'source_missing_terminal_mip' in info:
        require(allow_repair, 'Malformed terminal mips outside explicit facial repair allowlist')
        original = decode_blp(raw)
        missing = {k: v for k, v in info['source_missing_terminal_mip'].items()
                   if k != 'preserved_byte_exact'}
        raw = encode_blp(original)
        info = forest.validate_blp(raw)
        require(np.array_equal(decode_blp(raw), original), 'Repaired source top RGBA mismatch')
        require(info['mips'][-1]['width'] == info['mips'][-1]['height'] == 1,
                'Repaired source missing final1x1 mip')
        metadata.update(byte_exact=False, repair_type='terminal_mip_rebuild_encoding3_bgra',
                        source_missing_terminal_mip=missing, top_rgba_pixel_exact=True,
                        alpha_representation='straight RGBA, no keying or premultiplication',
                        generated_full_mips=True)
    # Every shipped texture must pass the original strict native-format checker.
    forest.validate_blp(raw)
    return raw, info, metadata


def largest_support(mask):
    seen = np.zeros_like(mask)
    largest = []
    sizes = []
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        queue, group = [(int(y), int(x))], []
        seen[y, x] = True
        while queue:
            yy, xx = queue.pop()
            group.append((yy, xx))
            for ny, nx in ((yy - 1, xx), (yy + 1, xx), (yy, xx - 1), (yy, xx + 1)):
                if (0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1]
                        and mask[ny, nx] and not seen[ny, nx]):
                    seen[ny, nx] = True
                    queue.append((ny, nx))
        sizes.append(len(group))
        if len(group) > len(largest):
            largest = group
    require(bool(largest), 'No fitted garment region')
    core = np.zeros_like(mask)
    for y, x in largest:
        core[y, x] = True
    padded = np.pad(core, 1)
    support = np.zeros_like(core)
    for y in range(3):
        for x in range(3):
            support |= padded[y:y + core.shape[0], x:x + core.shape[1]]
    return support, sorted(sizes, reverse=True)


def fit_garment(bodies, underwear, limits):
    b, u = np.asarray(bodies, np.float64), np.asarray(underwear, np.float64)
    require(b.shape == u.shape == (6, 128, 256, 3), 'Unexpected garment fit dimensions')
    bm, um = b.mean(0), u.mean(0)
    db, du = b - bm, u - um
    t = np.clip((db * du).sum(axis=(0, 3)) / np.maximum((db * db).sum(axis=(0, 3)), 1), 0, 1)
    alpha = 1 - t
    support, sizes = largest_support(alpha >= .5)
    alpha *= support
    alpha[alpha < .05] = 0
    alpha[alpha > .95] = 1
    a = alpha[:, :, None]
    foreground = np.clip((um - (1 - a) * bm) / np.maximum(a, .05), 0, 255)
    delta = np.abs(a[None] * foreground[None] + (1 - a[None]) * b - u)
    proof = dict(mean_abs=float(delta.mean()), p99_abs=float(np.quantile(delta, .99)),
                 max_abs=float(delta.max()), nonzero_alpha_pixels=int((alpha > 0).sum()),
                 opaque_pixels=int((alpha == 1).sum()), core_component_sizes=sizes[:10],
                 mae_max=limits['mae_max'], p99_max=limits['p99_max'], approximate=True)
    require(proof['mean_abs'] <= limits['mae_max'] and proof['p99_abs'] <= limits['p99_max'],
            'Native garment reconstruction exceeds pinned error limits')
    return foreground, a, proof


def crop(atlas, box):
    x0, y0, x1, y1 = box
    return atlas[y0:y1, x0:x1].copy()


def read_numeric(raw, fields):
    require(len(raw) >= 20, 'Truncated numeric DBC')
    magic, n, f, size, ns = struct.unpack_from('<4s4I', raw)
    require(magic == b'WDBC' and f == fields and size == 4 * fields
            and ns == 1 and len(raw) == 20 + n * size + ns and raw[-1:] == b'\0',
            'Invalid numeric DBC')
    return [struct.unpack_from('<' + str(fields) + 'I', raw, 20 + i * size) for i in range(n)]


def numeric_dbc(rows, fields):
    return (struct.pack('<4s4I', b'WDBC', len(rows), fields, fields * 4, 1)
            + b''.join(struct.pack('<' + str(fields) + 'I', *r) for r in rows) + b'\0')


def hair_changes(native, strings):
    before, after = [], []
    for r in native:
        if r[1] != 8 or r[3] != 3 or r[2] not in (0, 1):
            continue
        if r[8] not in range(6 if r[2] == 0 else 5, 10):
            continue
        require(0 <= r[9] <= 12 and r[7] == (0x12 if r[9] < 10 else 0x06),
                'Unexpected native barber-only hair row')
        before.append(r)
        after.append((*r[:7], r[7] | 1, *r[8:]))
    require(len(after) == 117, 'Expected117 hair changes')
    return {r[0]: r for r in after}, [dict(before=list(forest.decode(b, strings)),
                                        after=list(forest.decode(a, strings)))
                                   for b, a in zip(before, after)]


def style_delta(source, native):
    selected = sorted([r for r in source if r[0] == 8 and
                       ((r[1] == 0 and r[2] in (11, 12, 13)) or
                        (r[1] == 1 and r[2] in (6, 7, 8, 9)))], key=lambda r: r[:3])
    delta = [(*r[:3], *r[6:9], 0, 0) for r in selected]
    expected = [(8, 0, v, 0, g, 0, 0, 0) for v, g in zip((11, 12, 13), (2, 4, 6))]
    expected += [(8, 1, v, 0, g, 0, 0, 0) for v, g in zip((6, 7, 8, 9), (2, 3, 4, 5))]
    require(delta == expected and len(native) == 222, 'Unexpected natural-style delta/baseline')
    require(not {r[:3] for r in native}.intersection(r[:3] for r in delta), 'Natural-style collision')
    return delta


def render_sql(rows, rollback=False):
    # Reuse the accepted guards/transaction machinery without editing its source.
    sql = forest.render_sql(rows, rollback)
    sql = sql.replace('azerothcore_setup_forest_troll_skins', 'azerothcore_setup_troll_customizations')
    sql = sql.replace('forest_troll_skins_expected', 'troll_customizations_expected')
    sql = sql.replace('tools/build_forest_troll_skins.py', 'tools/build_troll_customizations.py')
    sql = sql.replace('Native race8 ForestTroll additive overlay: IDs20000..20089, colors18..23.',
                      'Troll extension:247 new IDs20100..20346 +117 exact native hair overrides; preserves Forest90.')
    sql = sql.replace('ForestTroll:', 'Troll customizations:')
    for col in forest.COLS:
        if col.startswith('Texture'):
            sql = sql.replace(f'BINARY a.`{col}` <=> BINARY e.`{col}`',
                              f'CAST(a.`{col}` AS BINARY) <=> CAST(e.`{col}` AS BINARY)')
    return sql


def build(output, turtle=Path('/home/dev/wow-turtle'), native=Path('/home/dev/wow-335')):
    m = json.loads(MANIFEST.read_text())
    old = json.loads(forest.MANIFEST.read_text())
    require(sha(forest.MANIFEST) == m['accepted_manifest_sha256'], 'Accepted manifest changed')
    require(np.__version__ == '2.2.6' and Image.__version__ == '13.0.0', 'Use pinned requirements')
    output = output.resolve()
    require(not output.exists(), 'Output must be a fresh directory')
    require(not any(output.is_relative_to(p.resolve()) for p in (turtle, native)),
            'Output overlaps read-only reference client')
    require(m['target'] == dict(namespace='Character\\Custom\\TurtleTroll', id_first=20100,
                                id_last=20346, flags=17, male_colors=[24, 35], female_colors=[24, 32]),
            'Unsupported target allocation')
    roots = {'turtle': turtle, '335': native}
    archives, inputs = {}, {}
    for name, spec in {**old['archives'], **m['archives']}.items():
        path = roots[spec['client']] / spec['path']
        require(sha(path) == spec['sha256'], 'Archive hash mismatch: ' + str(path))
        archives[name], inputs[name] = path, dict(spec, bytes=path.stat().st_size)
    output.mkdir(parents=True)
    (output / 'Data').mkdir()
    resources, provenance, payload = [], [], {}
    with tempfile.TemporaryDirectory(prefix='troll-customizations-') as temp:
        stage = Path(temp)

        def source(archive, member):
            raw = forest.extract(archives[archive], member, stage / 'extract')
            provenance.append(dict(archive=archive, member=member, bytes=len(raw), sha256=digest(raw)))
            return raw

        def texture(archive, member, target):
            if target not in payload:
                raw = source(archive, member)
                try:
                    raw, info, metadata = prepare_texture(
                        raw, archive == 'female_textures' and member in m['repair_terminal_mips'])
                except ValueError as exc:
                    raise ValueError(f'{archive}:{member}: {exc}') from exc
                payload[target] = raw
                resources.append(dict(member=target, source_archive=archive, source_member=member,
                                      sha256=digest(raw), bytes=len(raw), **metadata, **info))
            return payload[target]

        def generated(target, rgba, derivation):
            raw = encode_blp(rgba)
            require(np.array_equal(decode_blp(raw), rgba), 'Generated BLP top mip mismatch')
            payload[target] = raw
            resources.append(dict(member=target, sha256=digest(raw), bytes=len(raw),
                                  byte_exact=False, derivation=derivation, **forest.validate_blp(raw)))

        srcraw = source('turtle_sections', old['sections']['member'])
        natraw = source('native_sections', old['sections']['member'])
        require(digest(srcraw) == old['sections']['turtle_sha256'] and
                digest(natraw) == old['sections']['native_sha256'], 'CharSections hash mismatch')
        sr, ss = forest.read_dbc(srcraw)
        nr, ns = forest.read_dbc(natraw)
        require(len(sr) == 6617 and len(nr) == 8958, 'Unexpected CharSections counts')
        selected = forest.select_source(sr, ss)
        accepted = forest.make_delta(selected, old)
        v1raw, _ = forest.merge(nr, ns, accepted)
        ar, astr = forest.read_dbc(v1raw)
        source_to_target = [dict(source_id=s[0], target_id=d[0], race=d[1], sex=d[2], base=d[3],
                                 variation=d[8], source_color=s[9], color=d[9], flags=d[7],
                                 textures=list(d[4:7])) for s, d in zip(selected, accepted)]
        for r in selected:
            for name in r[4:7]:
                if name:
                    texture('male_textures' if '\\Male\\' in name else 'female_textures', name,
                            forest.relocated(name, old['target']['namespace']))
        require(len(payload) == 162, 'Accepted texture inventory changed')
        accepted_resources = {name: digest(raw) for name, raw in payload.items()}
        # Reconstruct v1 directly from original sources, prove its authoritative MPQ hash.
        v1payload = dict(payload)
        v1payload[old['sections']['member']] = v1raw
        create_mpq(stage / 'v1.MPQ', v1payload, stage)
        require(sha(stage / 'v1.MPQ') == m['v1']['Data/patch-S.MPQ'], 'Accepted v1 reconstruction changed')

        fitted, garment_proof = {}, []
        for sex, label in enumerate(('Male', 'Female')):
            for component, boxkey in [('NakedPelvisSkin', 'pelvis_box')] + (
                    [('NakedTorsoSkin', 'torso_box')] if sex else []):
                bodies, underwear = [], []
                for color in range(6):
                    stem = f'Character\\Troll\\{label}\\Troll{label}'
                    body = decode_blp(source('native_textures', stem + f'Skin00_{color:02}.blp'))
                    cloth = decode_blp(source('native_textures', stem + f'{component}00_{color:02}.blp'))
                    require(body.shape == (512, 512, 4) and cloth.shape == (128, 256, 4),
                            'Native garment/body dimensions changed')
                    bodies.append(crop(body, m['garment'][boxkey])[:, :, :3])
                    underwear.append(cloth[:, :, :3])
                f, a, proof = fit_garment(bodies, underwear, m['garment'])
                fitted[sex, component] = f, a
                garment_proof.append(dict(sex=sex, component=component,
                                          native_512_box=m['garment'][boxkey], **proof))

        new, fixed_faces, body_mappings = [], [], []
        namespace = m['target']['namespace']
        decoded_source = [forest.decode(r, ss, 'turtle') for r in sr]
        for sex, label in enumerate(('Male', 'Female')):
            body_rows = [r for r in decoded_source if r[1] == 8 and r[2] == sex and r[3] == 0
                         and r[0] in range(*( (4768, 4777) if sex == 0 else (5111, 5120) ))]
            require(len(body_rows) == 9 and [r[9] for r in body_rows] == list(range(9))
                    and all(r[7] == 1 for r in body_rows), 'Alternate body source mismatch')
            bodies = []
            for number, r in zip(range(100, 109), body_rows):
                require(r[4] == f'Character\\Troll\\{label}\\Troll{label}Skin00_{number}.blp',
                        'Unexpected alternate body path')
                archive = 'turtle_sections' if number in m['alternates']['patch8_' + label.lower()] else 'turtle_texture'
                bodies.append((str(number), archive, r[4], r[0]))
            if sex == 0:
                bodies += [(name, 'turtle_shop', f'textures\\bakednpctextures\\{name}.blp', None)
                           for name in m['shops']]
            for color, (name, archive, member, source_id) in enumerate(bodies, 24):
                prefix = f'{namespace}\\{label}\\{name}'
                bodytarget = prefix + '_Body.blp'
                bodyraw = texture(archive, member, bodytarget)
                atlas = decode_blp(bodyraw)
                require(atlas.shape[:2] == ((512, 512) if name in m['shops'][:2] else (256, 256)),
                        'Unexpected source body dimensions')
                if atlas.shape[0] == 256:
                    atlas = atlas.repeat(2, 0).repeat(2, 1)
                lower, upper = prefix + '_FaceLower.blp', prefix + '_FaceUpper.blp'
                generated(lower, crop(atlas, (0, 384, 256, 512)), 'same body atlas lower-face crop')
                generated(upper, crop(atlas, (0, 320, 256, 384)), 'same body atlas upper-face crop')
                clothes = []
                for component, boxkey in [('NakedPelvisSkin', 'pelvis_box')] + (
                        [('NakedTorsoSkin', 'torso_box')] if sex else []):
                    rgba = crop(atlas, m['garment'][boxkey])
                    f, a = fitted[sex, component]
                    rgba[:, :, :3] = np.rint(a * f + (1 - a) * rgba[:, :, :3]).clip(0, 255).astype(np.uint8)
                    target = prefix + '_' + component + '.blp'
                    generated(target, rgba, 'fitted native cloth over same effective body crop; approximate')
                    clothes.append(target)
                new.append((0, 8, sex, 0, bodytarget, '', '', 17, 0, color))
                for face in range(5 + sex):
                    new.append((0, 8, sex, 1, lower, upper, '', 17, face, color))
                new.append((0, 8, sex, 4, clothes[0], clothes[1] if sex else '', '', 17, 0, color))
                fixed_faces.append(dict(sex=sex, color=color, faces=list(range(5 + sex)),
                                        distinct_authored_faces=1, textures=[lower, upper], source_body=member))
                body_mappings.append(dict(sex=sex, color=color, source_id=source_id,
                                          source_archive=archive, source_member=member, member=bodytarget))
        require(len(new) == 156, 'Expected156 body/face/underwear rows')
        alias = source('male_textures', 'Character\\Troll\\Male\\TrollMaleSkin00_109.blp')
        forestbody = next(r[4] for r in accepted if r[0] == 20000)
        require(alias == payload[forestbody], 'Male109 is no longer exact Forest18 alias')

        dk_aliases = []
        for sex, variations in ((0, (11, 12, 13)), (1, (6, 7, 8, 9))):
            facials = [r for r in decoded_source if r[1] == 8 and r[2] == sex and r[3] == 2
                       and r[8] in variations]
            require(len(facials) == 10 * len(variations) and all(r[7] == 0 for r in facials),
                    'Incomplete new facial family')
            lookup = {(r[8], r[9]): r for r in facials}
            for var in variations:
                for color in range(13):
                    source_color = color if color < 10 else m['facials']['dk_aliases'][str(color)]
                    r = lookup[var, source_color]
                    refs = []
                    for member in r[4:7]:
                        target = forest.relocated(member, namespace)
                        if member:
                            raw = texture('female_textures', member, target)
                            require(raw[:4] == b'BLP2' and raw[9] == 8 and
                                    (raw[8] == 1 or (member in m['repair_terminal_mips'] and raw[8] == 3)),
                                    'Expected true-alpha facial BLP2')
                            decode_blp(raw)
                        refs.append(target)
                    new.append((0, 8, sex, 2, *refs, 17, var, color))
                    if color >= 10:
                        dk_aliases.append(dict(sex=sex, variation=var, color=color,
                                               source_color=source_color, source_id=r[0]))
        new = [(20100 + i, *r[1:]) for i, r in enumerate(sorted(new, key=forest.key))]
        require(len(new) == 247 and new[-1][0] == 20346, 'New row allocation mismatch')
        changed, hair = hair_changes(nr, ns)
        modified = [changed.get(r[0], r) for r in ar]
        merged, duplicates = forest.merge(modified, astr, new)
        final, finalstrings = forest.read_dbc(merged)
        finalids = {r[0]: r for r in final}
        require(len(final) == 9295 and all(finalids[r[0]] == changed.get(r[0], r) for r in nr),
                'Native preservation failed')
        require(all(finalids[r[0]] == r for r in ar if 20000 <= r[0] <= 20089),
                'Accepted90 raw records changed')
        require(all(digest(payload[n]) == h for n, h in accepted_resources.items()),
                'Accepted162 texture bytes changed')
        repairs = [r for r in resources if 'repair_type' in r]
        require(sorted(r['source_member'] for r in repairs) == sorted(m['repair_terminal_mips']),
                'Expected exactly the two pinned facial mip repairs')
        for resource in resources:
            forest.validate_blp(payload[resource['member']])
        payload[old['sections']['member']] = merged
        stylesource = source('turtle_styles', m['styles']['member'])
        stylenative = source('native_styles', m['styles']['member'])
        require(digest(stylesource) == m['styles']['turtle_sha256'] and
                digest(stylenative) == m['styles']['native_sha256'], 'Natural-style hash mismatch')
        native_styles = read_numeric(stylenative, 8)
        styles = style_delta(read_numeric(stylesource, 9), native_styles)
        compact = numeric_dbc(styles, 8)
        payload[m['styles']['member']] = numeric_dbc(native_styles + styles, 8)
        patch = output / 'Data/patch-S.MPQ'
        create_mpq(patch, payload, stage)
        repeat = stage / 'repeat.MPQ'
        create_mpq(repeat, payload, stage)
        require(sha(patch) == sha(repeat), 'Nondeterministic MPQ')
        overlays = sorted(new + [tuple(h['after']) for h in hair], key=forest.key)
        sql, rollback = render_sql(overlays), render_sql(overlays, True)
        delta, _ = forest.merge([], b'\0', overlays)
        (output / 'CharSections.delta.dbc').write_bytes(delta)
        (output / 'CharacterFacialHairStyles.dbc').write_bytes(compact)
        (output / 'turtle_troll_customizations.sql').write_text(sql)
        (output / 'rollback.sql').write_text(rollback)
        report = dict(version=2, feature=m['feature'], manifest_sha256=sha(MANIFEST),
                      accepted_manifest_sha256=sha(forest.MANIFEST), inputs=inputs,
                      provenance=provenance, decisions=m['decisions'],
                      counts=dict(native_rows=8958, accepted_rows=90, added_rows=247,
                                  new_skin_rows=156, new_facial_rows=91, hair_modified_rows=117,
                                  sql_rows=364, final_rows=9295, new_body_resources=21,
                                  natural_style_added_rows=7, natural_style_final_rows=229,
                                  accepted_textures=162, textures=len(resources), payload_members=len(payload)),
                      preservation=dict(accepted90_record_bytes=True, accepted162_texture_bytes=True,
                                        original_string_prefix=True, native_only117_player_bit_changes=True,
                                        v1_reconstructed_sha256=sha(stage / 'v1.MPQ'),
                                        baseline_duplicate_tuples=duplicates),
                      source_to_target=source_to_target, body_mappings=body_mappings,
                      fixed_face_aliases=fixed_faces, dk_facial_color_aliases=dk_aliases,
                      body_aliases=[dict(source_id=4777, source_number=109, target_id=20000,
                                         color=18, sha256=digest(alias))],
                      garment_reconstruction=garment_proof, hair_changes=hair,
                      new_rows=[list(r) for r in new], sql_rows=[list(r) for r in overlays],
                      natural_style_rows=[list(r) for r in styles], resources=resources,
                      patch_sha256=sha(patch), charsections_sha256=digest(merged),
                      natural_styles_sha256=digest(payload[m['styles']['member']]),
                      server_natural_styles_sha256=digest(compact), delta_dbc_sha256=digest(delta),
                      sql_sha256=digest(sql.encode()), rollback_sha256=digest(rollback.encode()),
                      mpq_tool_sha256=sha(forest.MPQ),
                      validations=dict(all_payload_members_roundtrip=True, two_mpq_creates_identical=True,
                                       all_shipped_blps_strict_native_valid=True,
                                       repaired_source_top_rgba_pixel_exact=True,
                                       generated_blp_top_mips_roundtrip=True, runtime_db_checked=False,
                                       runtime_or_visual_acceptance=False),
                      mpq_members={name: len(raw) for name, raw in sorted(payload.items())})
        (output / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        names = ('Data/patch-S.MPQ', 'report.json', 'CharSections.delta.dbc',
                 'CharacterFacialHairStyles.dbc', 'turtle_troll_customizations.sql', 'rollback.sql')
        (output / 'SHA256SUMS').write_text(''.join(f'{sha(output / n)}  {n}\n' for n in names))
    return report


def create_mpq(patch, payload, stage):
    entries = []
    for i, (name, raw) in enumerate(sorted(payload.items())):
        path = stage / f'member-{i}'
        path.write_bytes(raw)
        os.utime(path, (0, 0))
        entries.append(f'{path}|{name}')
    listing = stage / 'create.txt'
    listing.write_text('\n'.join(entries) + '\n')
    forest.command('create', patch, listing)
    members = {}
    for line in forest.command('list', patch).splitlines():
        name, size = line.rsplit('\t', 1)
        require(name not in members, 'Duplicate MPQ member')
        members[name] = int(size)
    require(set(members) == set(payload) | {'(listfile)'}, 'MPQ inventory mismatch')
    for name, raw in payload.items():
        require(members[name] == len(raw) and forest.extract(patch, name, stage / 'roundtrip') == raw,
                'MPQ roundtrip mismatch: ' + name)


def verify_publication(target, pins=None):
    """Refuse partial/corrupt publications, including mismatched reports/checksums."""
    for name in ('Data/patch-S.MPQ', 'report.json', 'SHA256SUMS'):
        require((target / name).is_file() and not (target / name).is_symlink(), 'Missing/linked publication: ' + name)
        if pins:
            require(sha(target / name) == pins[name], 'Unknown v1 artifact: ' + name)
    report = json.loads((target / 'report.json').read_text())
    require(report['patch_sha256'] == sha(target / 'Data/patch-S.MPQ'), 'Published report hash mismatch')
    expected = ''.join(f'{sha(target / n)}  {n}\n' for n in ('Data/patch-S.MPQ', 'report.json'))
    require((target / 'SHA256SUMS').read_text() == expected, 'Published checksums mismatch')
    return report


def publish(output, target=None):
    target = target or ROOT / 'client_patches/turtle_forest_troll'
    m = json.loads(MANIFEST.read_text())
    report = json.loads((output / 'report.json').read_text())
    require(report['manifest_sha256'] == sha(MANIFEST), 'Output manifest mismatch')
    products = {'Data/patch-S.MPQ': 'patch_sha256', 'turtle_troll_customizations.sql': 'sql_sha256',
                'rollback.sql': 'rollback_sha256', 'CharacterFacialHairStyles.dbc': 'server_natural_styles_sha256'}
    for name, key in products.items():
        require(sha(output / name) == report[key], 'Output hash mismatch: ' + name)
    current = verify_publication(target)
    if current['patch_sha256'] != m['v1']['Data/patch-S.MPQ']:
        identity = dict(patch_sha256=current['patch_sha256'], report_sha256=sha(target / 'report.json'),
                        manifest_sha256=current.get('manifest_sha256'))
        generated_identity = dict(patch_sha256=report['patch_sha256'], report_sha256=sha(output / 'report.json'),
                                  manifest_sha256=report['manifest_sha256'])
        require(current.get('version') == 2 and (identity == generated_identity or
                identity in m['previous_v2_publications']), 'Refusing unknown current patch-S')
    else:
        verify_publication(target, m['v1'])
    backup = target / 'v1'
    if backup.exists():
        verify_publication(backup, m['v1'])
    else:
        verify_publication(target, m['v1'])
        backup.mkdir()
        (backup / 'Data').mkdir()
        for name in m['v1']:
            shutil.copyfile(target / name, backup / name)
        verify_publication(backup, m['v1'])
    destinations = {'Data/patch-S.MPQ': target / 'Data/patch-S.MPQ',
                    'report.json': target / 'report.json',
                    'turtle_troll_customizations.sql': ROOT / 'data/sql/custom/db_world/turtle_troll_customizations.sql',
                    'rollback.sql': ROOT / 'data/sql/rollback/turtle_troll_customizations.sql',
                    'CharacterFacialHairStyles.dbc': ROOT / 'data/server/turtle-customizations/dbc/CharacterFacialHairStyles.dbc'}
    for name, dest in destinations.items():
        if dest.exists() and name not in ('Data/patch-S.MPQ', 'report.json'):
            require(dest.read_bytes() == (output / name).read_bytes(), 'Refusing differing generated artifact: ' + str(dest))
        staging = dest.with_name(dest.name + '.tmp')
        require(not staging.exists() and not staging.is_symlink(), 'Stale publish staging file: ' + str(staging))
    # Preflight ALL paths, then stage ALL products before replacing any existing
    # artifact. A predictable later refusal must not leave a mixed publication.
    for name, dest in destinations.items():
        dest.parent.mkdir(parents=True, exist_ok=True)
        staging = dest.with_name(dest.name + '.tmp')
        shutil.copyfile(output / name, staging)
    for dest in destinations.values():
        staging = dest.with_name(dest.name + '.tmp')
        staging.replace(dest)
    (target / 'SHA256SUMS').write_text(''.join(f'{sha(target / n)}  {n}\n'
                                            for n in ('Data/patch-S.MPQ', 'report.json')))
    verify_publication(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--turtle-client', type=Path, default=Path('/home/dev/wow-turtle'))
    parser.add_argument('--native-client', type=Path, default=Path('/home/dev/wow-335'))
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    report = build(args.output, args.turtle_client, args.native_client)
    if args.publish:
        publish(args.output)
    print(json.dumps(dict(output=str(args.output), counts=report['counts'],
                          patch_sha256=report['patch_sha256']), indent=2))


if __name__ == '__main__':
    main()
