#!/usr/bin/env python3
"""Compare a local-space ray through the removed box against both WMO meshes.

This verifies geometry only, not client movement or live server line of sight.
"""
import argparse
from pathlib import Path

from crypt_collision_fix import group, records


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def intersects(a, b, c):
    origin, direction = (19., 3., -7.), (0., 6., 0.)
    e1, e2 = sub(b, a), sub(c, a)
    h = cross(direction, e2)
    det = dot(e1, h)
    if abs(det) < 1e-8:
        return False
    s = sub(origin, a)
    u = dot(s, h) / det
    q = cross(s, e1)
    v, t = dot(direction, q) / det, dot(e2, q) / det
    return 0 <= u <= 1 and 0 <= v and u+v <= 1 and 0 <= t <= 1


def hits(path):
    _, _, parts = group(path.read_bytes())
    vertices = records(parts['MOVT'], '<3f')
    return [i for i, tri in enumerate(records(parts['MOVI'], '<3H'))
            if intersects(*(vertices[j] for j in tri))]


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('original', type=Path)
    ap.add_argument('corrected', type=Path)
    args = ap.parse_args()
    before, after = hits(args.original), hits(args.corrected)
    print(f'Original ray intersections: {before}; corrected: {after}')
    assert len(before) == 2 and not after, 'Passage ray did not meet expectations'
