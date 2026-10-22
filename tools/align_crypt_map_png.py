#!/usr/bin/env python3
"""Align a manually edited map to the exported original without editing inputs.

Accepts only a well-supported small similarity transform. Writes the aligned
PNG and evidence into a new directory for review before reimport.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

REFERENCE_SHA = '4f471f14eca09a2c17a2c2865e1d0ca97ff19312eddd53cdc8468b11c964bdf4'


def load(path):
    data = path.read_bytes()
    with Image.open(path) as im:
        if im.format != 'PNG' or im.mode != 'RGBA' or im.size != (1024, 768):
            raise ValueError('Expected a 1024x768 RGBA PNG')
        return data, np.array(im)


def align_pixels(original, edited, transform):
    """Reject cropped content and preserve original pixels at marginal edges.

    Lanczos4 samples floor(p)-3 through floor(p)+4. Invalid support at the
    canvas edge must not turn a valid original map pixel into opaque black.
    """
    h, w = original.shape[:2]
    sy, sx = np.indices((h, w), dtype='float32')
    px = transform[0, 0]*sx + transform[0, 1]*sy + transform[0, 2]
    py = transform[1, 0]*sx + transform[1, 1]*sy + transform[1, 2]
    visible = original[:, :, 3] > 0
    supported = (px >= 3) & (px < edited.shape[1]-4) & (py >= 3) & (py < edited.shape[0]-4)
    # Transparent padding may begin inside the canvas. It is not valid color
    # support for an opaque destination pixel either.
    source_support = cv2.erode((edited[:, :, 3] > 0).astype('uint8'),
                               np.ones((8, 8), dtype='uint8'), anchor=(3, 3),
                               borderType=cv2.BORDER_CONSTANT, borderValue=0)
    ix = np.clip(np.floor(px).astype('int32'), 0, edited.shape[1]-1)
    iy = np.clip(np.floor(py).astype('int32'), 0, edited.shape[0]-1)
    supported &= source_support[iy, ix] > 0
    in_canvas = (px >= 0) & (px <= edited.shape[1]-1) & (py >= 0) & (py <= edited.shape[0]-1)
    total = int(visible.sum())
    if not total:
        raise ValueError('Original map has no visible pixels')
    restored = int((visible & ~supported).sum())
    outside = int((visible & ~in_canvas).sum())
    if restored / total > 0.02 or outside / total > 0.005:
        raise ValueError('Edited image clips significant original map content')
    rgb = cv2.warpAffine(edited[:, :, :3], transform, (w, h),
                         flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP,
                         borderMode=cv2.BORDER_REFLECT_101)
    keep_original = ~visible | ~supported
    rgb[keep_original] = original[:, :, :3][keep_original]
    return np.dstack((rgb, original[:, :, 3])), dict(
        visible_pixels=total, restored_boundary_pixels=restored,
        outside_canvas_pixels=outside, restored_fraction=restored/total,
        outside_canvas_fraction=outside/total,
        boundary_policy='Preserve original pixels without full Lanczos support')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--image', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise ValueError('Output must be a new directory')
    reference_bytes, original = load(args.reference)
    image_bytes, edited = load(args.image)
    if hashlib.sha256(reference_bytes).hexdigest() != REFERENCE_SHA:
        raise ValueError('Unexpected original map reference')
    cv2.setRNGSeed(0)
    sift = cv2.SIFT_create()
    ka, da = sift.detectAndCompute(cv2.cvtColor(original[:, :, :3], cv2.COLOR_RGB2GRAY),
                                  (original[:, :, 3] > 0).astype('uint8') * 255)
    kb, db = sift.detectAndCompute(cv2.cvtColor(edited[:, :, :3], cv2.COLOR_RGB2GRAY),
                                  (edited[:, :, 3] > 0).astype('uint8') * 255)
    if da is None or db is None or len(db) < 2:
        raise ValueError('Insufficient map details for registration')
    pairs = cv2.BFMatcher().knnMatch(da, db, k=2)
    good = [m for pair in pairs if len(pair) == 2 for m, n in [pair]
            if m.distance < 0.7 * n.distance]
    if len(good) < 100:
        raise ValueError('Insufficient matching map features')
    src = np.float32([ka[m.queryIdx].pt for m in good])
    dst = np.float32([kb[m.trainIdx].pt for m in good])
    transform, mask = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC,
                                               ransacReprojThreshold=2)
    if transform is None or mask is None:
        raise ValueError('Could not determine map transform')
    inliers = mask.ravel() > 0
    errors = np.linalg.norm(src @ transform[:, :2].T + transform[:, 2] - dst, axis=1)
    scale = float(np.linalg.norm(transform[:, 0]))
    rotation = float(np.degrees(np.arctan2(transform[1, 0], transform[0, 0])))
    span = np.ptp(src[inliers], axis=0)
    if not (inliers.sum() >= 100 and inliers.mean() >= 0.7
            and span[0] > 800 and span[1] > 500
            and np.percentile(errors[inliers], 95) < 2
            and 0.9 < scale < 1.1 and abs(rotation) < 1
            and np.max(np.abs(transform[:, 2])) < 10):
        raise ValueError('Registration exceeds safe small-transform bounds; inspect manually')
    # For each original canvas pixel, sample its corresponding edited-image
    # coordinate. WARP_INVERSE_MAP uses this original->edited transform.
    aligned, coverage = align_pixels(original, edited, transform)
    if args.image.read_bytes() != image_bytes or args.reference.read_bytes() != reference_bytes:
        raise ValueError('An input changed during processing')
    args.output.mkdir(parents=True)
    output = args.output / 'fixed-es-aligned.png'
    Image.fromarray(aligned).save(output)
    report = dict(source_sha256=hashlib.sha256(image_bytes).hexdigest(),
                  reference_sha256=REFERENCE_SHA,
                  aligned_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                  original_to_edited_transform=transform.tolist(), scale=scale,
                  rotation_degrees=rotation, feature_matches=len(good),
                  inliers=int(inliers.sum()), inlier_span=span.tolist(),
                  median_error=float(np.median(errors[inliers])),
                  p95_error=float(np.percentile(errors[inliers], 95)),
                  alpha_preserved_exactly=True, inputs_modified=False,
                  coverage=coverage,
                  operation='Global registration/resampling only; no label repaint')
    (args.output / 'alignment.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
