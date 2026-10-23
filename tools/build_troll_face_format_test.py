#!/usr/bin/env python3
"""Bounded A/B candidate: change exactly two male skin24 face textures.

Never publishes over the normal patch-S or installs into a client/server.
Uses the pinned published v2 only, not the original clients or research files.
Top-level RGBA must be lossless in a 256-colour palette; lower mips may have
palette approximation, which is measured. Runtime acceptance is not implied.
"""
import argparse
import json
from pathlib import Path
import struct
import tempfile

import numpy as np

import build_troll_customizations as troll
from crypt_release_client import members, key

ROOT = troll.ROOT
BASE = ROOT / 'client_patches/turtle_forest_troll'
SOURCE = BASE / 'v2' if (BASE / 'v2').exists() else BASE
BASE_SHA = 'd63ecb0e583a77f4283dde8f39e253d4dee5694f6978ae5326d1120e164165a9'
FACES = tuple(r'Character\Custom\TurtleTroll\Male\100_Face' + part + '.blp'
              for part in ('Lower', 'Upper'))
REFERENCE = r'Character\Custom\TurtleForestTroll\Male\ForestTrollMaleFaceLower00_00.blp'


def palette_encode(original, allow_quantize=False):
    """Keep each top pixel and all alpha exactly; shared palette across mips."""
    info = troll.forest.validate_blp(original)
    troll.require(original[8] == 3, 'Expected generated BGRA face')
    images = [troll.decode_blp(original, i) for i in range(len(info['mips']))]
    top = images[0]
    palette, inverse = np.unique(top[:, :, :3].reshape(-1, 3), axis=0, return_inverse=True)
    quantized = len(palette) > 256
    troll.require(not quantized or allow_quantize, 'Top RGB cannot be represented losslessly by a palette')
    if quantized:
        troll.require(troll.Image.__version__ == '13.0.0', 'Use pinned Pillow for quantization')
        image = troll.Image.fromarray(top[:, :, :3]).quantize(
            colors=256, method=troll.Image.Quantize.MEDIANCUT, dither=troll.Image.Dither.NONE)
        palette = np.unique(np.asarray(image.convert('RGB')).reshape(-1, 3), axis=0)
    depth = 0 if all(np.all(image[:, :, 3] == 255) for image in images) else 8
    colours = np.zeros((256, 4), dtype=np.uint8)
    colours[:len(palette), :3] = palette[:, [2, 1, 0]]
    offsets, sizes, data, metrics = [0] * 16, [0] * 16, [], []
    offset = 1172
    for level, image in enumerate(images):
        rgb = image[:, :, :3].reshape(-1, 3)
        if level == 0 and not quantized:
            indices = inverse.astype(np.uint8)
        else:
            # Explicit nearest palette colour; deterministic tie-break by sorted
            # RGB order. Bounded chunks avoid a huge pixel-by-palette allocation.
            chunks = []
            for start in range(0, len(rgb), 2048):
                diff = rgb[start:start + 2048, None, :].astype(np.int32) - palette[None].astype(np.int32)
                chunks.append(np.argmin((diff * diff).sum(axis=2), axis=1).astype(np.uint8))
            indices = np.concatenate(chunks)
        reconstructed = palette[indices]
        error = np.abs(reconstructed.astype(np.int16) - rgb.astype(np.int16))
        chunk = indices.tobytes()
        if depth:
            chunk += image[:, :, 3].tobytes()
        offsets[level], sizes[level] = offset, len(chunk)
        data.append(chunk)
        offset += len(chunk)
        metrics.append(dict(level=level, rgb_mae=float(error.mean()), rgb_max=int(error.max())))
        if quantized:
            metrics[-1]['rgb_p99'] = float(np.quantile(error, .99))
    height, width = top.shape[:2]
    # Same palettized representation/preferred format as accepted Forest faces.
    raw = (struct.pack('<4sI4B2I', b'BLP2', 1, 1, depth, 8, original[11], width, height)
           + struct.pack('<16I', *offsets) + struct.pack('<16I', *sizes)
           + colours.tobytes() + b''.join(data))
    after = troll.forest.validate_blp(raw)
    troll.require(len(after['mips']) == len(images), 'Mip count changed')
    troll.require(quantized or np.array_equal(troll.decode_blp(raw), top), 'Top RGBA changed')
    for level, image in enumerate(images):
        decoded = troll.decode_blp(raw, level)
        troll.require(decoded.shape == image.shape and
                      np.array_equal(decoded[:, :, 3], image[:, :, 3]), 'Mip shape/alpha changed')
    return raw, dict(palette_colours=len(palette), top_rgba_exact=not quantized, all_mip_alpha_exact=True,
                     before=dict(encoding=original[8], alpha_bits=original[9], preferred_format=original[10],
                                 width=width, height=height, first_mip_offset=info['mips'][0]['offset']),
                     after=dict(encoding=1, alpha_bits=depth, preferred_format=8,
                                width=width, height=height, first_mip_offset=1172), mip_errors=metrics)


def build(output):
    output = Path(output).absolute()
    troll.require(not output.exists(), 'Output must be fresh')
    # Outputs must remain research/test artifacts; never point at a game client
    # or normal publication. These two roots are the only permitted locations.
    allowed = ((ROOT / 'work').resolve(), (BASE / 'face-format-test').resolve())
    resolved = output.resolve()
    troll.require((resolved.is_relative_to(allowed[0]) and resolved != allowed[0])
                  or resolved == allowed[1], 'Choose a new work subdirectory or the dedicated test directory')
    baseline = SOURCE / 'Data/patch-S.MPQ'
    troll.require(troll.sha(baseline) == BASE_SHA, 'Normal v2 baseline hash mismatch')
    original = members(troll.forest.MPQ, baseline)
    reference = original[key(REFERENCE)][1]
    troll.require(reference[8] == 1 and reference[10] == 8, 'Accepted reference palette format changed')
    payload = {name: data for name, data in original.values()}
    changed = []
    for name in FACES:
        actual_name, before = original[key(name)]
        after, report = palette_encode(before)
        payload[actual_name] = after
        changed.append(dict(member=actual_name, before_sha256=troll.digest(before),
                            after_sha256=troll.digest(after), **report))
    output.mkdir(parents=True)
    (output / 'Data').mkdir()
    with tempfile.TemporaryDirectory(prefix='troll-face-ab-') as temp:
        stage = Path(temp)
        patch = output / 'Data/patch-S.MPQ'
        troll.create_mpq(patch, payload, stage)
        repeat = stage / 'repeat.MPQ'
        troll.create_mpq(repeat, payload, stage)
        troll.require(troll.sha(patch) == troll.sha(repeat), 'Non-deterministic candidate')
    actual = members(troll.forest.MPQ, patch)
    troll.require(set(actual) == set(original), 'Member set changed')
    differences = [original[k][0] for k in original if original[k][1] != actual[k][1]]
    troll.require(set(differences) == set(FACES), 'Changes are not limited to the two selected face textures')
    troll.require(troll.sha(baseline) == BASE_SHA, 'Normal patch was modified')
    report = dict(kind='troll-face-format-ab', baseline_sha256=BASE_SHA,
                  candidate_sha256=troll.sha(patch), selected=dict(race=8, sex=0, skin=24,
                      source_number=100, description='male first v2 alternate, purple body',
                      faces_aliased=list(range(5))), changes=changed,
                  checks=dict(payload_members=len(actual), changed_members=2,
                              other_payloads_byte_exact=True, dbc_files_byte_exact=True,
                              normal_publication_unchanged=True, deterministic=True,
                              client_test_run=False, server_changed=False))
    (output / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    instructions = '''# Single face-format A/B test

This is a full replacement candidate for the owned patch-S v2, NOT an overlay
to load together with it. Only male Troll Skin24's FaceLower/FaceUpper differ.
The top-level RGBA pixels are identical; serialization changes to BLP2 palette.
Other skin faces remain unchanged and may still show the reported error.

1. Verify SHA256SUMS in this directory. Fully exit WoW.
2. Back up your current owned Data/patch-S.MPQ OUTSIDE Data. Baseline expected:
   d63ecb0e583a77f4283dde8f39e253d4dee5694f6978ae5326d1120e164165a9
3. Copy this candidate Data/patch-S.MPQ to that SAME client path. Keep T/Z and
   locale patches unchanged. Do not install another S alongside it or rename it
   to a higher-priority test archive. No SQL or server restart is necessary.
4. Select a male Troll of an ordinary class, the first additional v2 tone after
   the six Forest tones (purple body, source100 / internal Skin24). Any normal
   Face0..4 references this same pair. Choose an ORIGINAL tusk/facial option,
   not new face paint that could conceal the underlying face.
5. Compare exactly that selection before/after: does the face regain detail and
   match the purple body, or remain green/untextured? A screenshot is useful.
6. Fully exit WoW and restore your backed-up v2 S to revert this experiment.

Do not roll back the server, remove hairstyles/features, or replace with v1.
This artifact is an experiment, not an accepted repair of all v2 skins.
'''
    (output / 'INSTALL.md').write_text(instructions)
    names = ('Data/patch-S.MPQ', 'report.json', 'INSTALL.md')
    (output / 'SHA256SUMS').write_text(''.join(f'{troll.sha(output / name)}  {name}\n' for name in names))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BASE / 'face-format-test')
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps(dict(output=str(args.output), candidate_sha256=result['candidate_sha256'],
                          selected=result['selected'], checks=result['checks']), indent=2))
