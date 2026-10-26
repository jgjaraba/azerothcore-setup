"""Deterministic CPU-compatible BLP2 normalization; imports imaging only on use."""
import math
import struct


def normalize(raw):
    from PIL import Image, __version__
    import numpy as np
    from build_new_races_assets import blp_rgba, palette_rgba, require, sha
    from build_forest_troll_skins import validate_blp
    require(__version__ == '13.0.0' and np.__version__ == '2.2.6',
            'Install tools/troll-customizations-requirements.txt in the image venv')
    info = validate_blp(raw)
    decoded = [blp_rgba(raw, i) for i in range(len(info['mips']))]
    top = np.frombuffer(decoded[0], dtype=np.uint8).reshape(-1, 4)
    image = Image.frombytes('RGBA', (info['width'], info['height']), decoded[0]).convert('RGB')
    quantized = image.quantize(colors=256, method=Image.Quantize.MEDIANCUT,
                               dither=Image.Dither.NONE)
    entries = quantized.getpalette()
    palette = sorted(set(tuple(entries[i:i+3]) for i in range(0, len(entries), 3)))
    palette += [palette[-1]]*(256-len(palette))
    colors = np.array(palette, dtype=np.int32)
    # Exact nearest squared RGB distance; sorted palette + argmin gives stable ties.
    all_rgb = np.concatenate([np.frombuffer(r, dtype=np.uint8).reshape(-1, 4)[:, :3]
                              for r in decoded])
    unique, inverse = np.unique(all_rgb, axis=0, return_inverse=True)
    nearest = np.empty(len(unique), dtype=np.uint8)
    for start in range(0, len(unique), 1024):
        delta = unique[start:start+1024].astype(np.int32)[:, None, :] - colors[None, :, :]
        nearest[start:start+1024] = (delta*delta).sum(axis=2).argmin(axis=1)
    indices = nearest[inverse]
    depth = 0 if all(all(a == 255 for a in r[3::4]) for r in decoded) else 8
    offsets, sizes, chunks, cursor, pos = [], [], [], 1172, 0
    for rgba in decoded:
        count = len(rgba)//4
        chunk = indices[pos:pos+count].tobytes() + (rgba[3::4] if depth else b'')
        offsets.append(cursor); sizes.append(len(chunk)); chunks.append(chunk)
        cursor += len(chunk); pos += count
    header = struct.pack('<4sI4B2I', b'BLP2', 1, 1, depth, 0, raw[11], info['width'], info['height'])
    header += struct.pack('<16I', *(offsets+[0]*(16-len(offsets))))
    header += struct.pack('<16I', *(sizes+[0]*(16-len(sizes))))
    result = header + b''.join(bytes((b, g, r, 0)) for r, g, b in palette) + b''.join(chunks)
    out_info = validate_blp(result)
    require([(m['width'], m['height']) for m in info['mips']] ==
            [(m['width'], m['height']) for m in out_info['mips']], 'Mip shape drift')
    mip_proofs = []
    for i, rgba in enumerate(decoded):
        after = palette_rgba(result, i)
        require(rgba[3::4] == after[3::4], 'Mip alpha changed')
        mip_proofs.append({'level': i, 'width': info['mips'][i]['width'],
                          'height': info['mips'][i]['height'], 'alpha_sha256': sha(rgba[3::4]),
                          'transparent_texels': rgba[3::4].count(0), 'alpha_exact': True})
    after = np.frombuffer(palette_rgba(result), dtype=np.uint8).reshape(-1, 4)
    errors = np.abs(top[:, :3].astype(np.int16)-after[:, :3].astype(np.int16)).reshape(-1)
    metrics = {'mae': float(errors.mean()), 'p99': int(np.sort(errors)[math.ceil(.99*len(errors))-1]),
               'max': int(errors.max())}
    return result, {'source_sha256': sha(raw), 'final_sha256': sha(result),
                    'algorithm': 'Pillow13 MEDIANCUT256 no dither; sorted palette; exact nearest RGB squared stable ties',
                    'rgb_quantization_top': metrics, 'top_unique_rgb': len(np.unique(top[:, :3], axis=0)),
                    'alpha_depth': depth, 'mips': mip_proofs,
                    'rgb_lossless': False, 'original_mips_preserved_not_regenerated': True}
