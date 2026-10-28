#!/usr/bin/env python3
"""Independent v256/v264 particle integration checks using licensed local fixtures.

DOTNET=/path/dotnet python3 tools/test_m2_particles.py --output work/m2-particles/FRESH
Optional --native-oracle points at the unmodified v264 OracleTree.m2 from common-2.MPQ.
No archives, DBC or installation are written. Derived fixtures live only in --output.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess

from test_new_races_models import ROOT, array, pair, validate

FIXTURES = [
    (r'WORLD/KALIMDOR/KALIDAR/PASSIVEDOODADS/ORACLETREE/HIGHELTREE.M2',
     '60e87d8a3a315dfc69acd043d3f7d8a0da7d3cf1cb78d8d6c4b447fdd0fd2029'),
    (r'WORLD/EXPANSION01/DOODADS/GENERIC/BLOODELF/TREES/HIGHTELVENTREE02.M2',
     'baa800ab2d222101495456163880472fb58936e4a025686e014d193af990dde3'),
    (r'WORLD/EXPANSION01/DOODADS/GENERIC/BLOODELF/TENTS/BE_TENT05.M2',
     'af207ec59cf7321b8f7ef6afbc2f9d577eefe836550d042594fc602cd2fbca2b'),
    (r'WORLD/EXPANSION01/DOODADS/GHOSTLANDS/ARCH/ELVENLANDS_ARCH_01.M2',
     '46b58ad62a81634d101ff5924da2e22952938ce4c604cd2bb12f783346dd1f9b'),
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def unpack(b, fmt, offset=0):
    return struct.unpack_from('<' + fmt, b, offset)


def part_track(b, header, width):
    times = []
    nt, pt = pair(b, header + 4)
    nv, pv = pair(b, header + 12)
    assert nt == nv
    for i in range(nt):
        nk, pk = pair(b, pt + i * 8)
        nvk, pkv = pair(b, pv + i * 8)
        assert nk == nvk and pk + nk * 4 <= len(b) and pkv + nk * width <= len(b)
        times.append((list(unpack(b, 'I' * nk, pk)),
                      [b[pkv + k * width:pkv + (k + 1) * width] for k in range(nk)]))
    return times


def fake(b, record, offset, fmt):
    n, p = pair(record, offset)
    nv, pv = pair(record, offset + 8)
    width = struct.calcsize('<' + fmt)
    assert n == nv and p + n * 2 <= len(b) and pv + n * width <= len(b)
    return list(unpack(b, 'h' * n, p)), [unpack(b, fmt, pv + i * width) for i in range(n)]


def check_particles(source, target):
    a, b = source.read_bytes(), target.read_bytes()
    report = json.loads(Path(str(target) + '.report.json').read_text())
    old, new = array(a, 316, 504), array(b, 296, 476)
    assert len(old) == len(new)
    assert len(report.get('particleConversion', [])) == len(old)
    sequences = array(a, 28, 68)
    output_count = pair(b, 28)[0]
    keys_checked = 0
    for index, (x, y) in enumerate(zip(old, new)):
        assert x[:4] == y[:4] and x[8:24] == y[8:24]
        headtail = x[45]
        assert unpack(y, 'I', 4)[0] == unpack(x, 'I', 4)[0] | [0x20000, 0x40000, 0x60000][headtail]
        assert unpack(x, 'HH', 40) == unpack(y, 'BB', 40)
        assert y[42:44] == bytes(2) and x[44:52] == y[44:52]
        for off in (24, 32):
            n, p = pair(x, off)
            nn, pp = pair(y, off)
            assert a[p:p+n] == b[pp:pp+nn]
        for j in range(11):
            so = 476 if j == 10 else 52 + j * 28
            to = 456 if j == 10 else 52 + j * 20 + (4 if j >= 6 else 0) + (4 if j >= 7 else 0)
            assert x[so:so+4] == y[to:to+4]
            width = 1 if j == 10 else 4
            nt, pt = pair(x, so + 12)
            nv, pv = pair(x, so + 20)
            assert nt == nv
            ts = list(unpack(a, 'I' * nt, pt))
            vals = [a[pv+k*width:pv+(k+1)*width] for k in range(nt)]
            rows = part_track(b, pair(b, 296)[1] + index * 476 + to, width)
            glob = unpack(x, 'h', so + 2)[0]
            assert len(rows) == (0 if not nt else 1 if glob >= 0 else output_count)
            if not nt:
                continue
            if glob >= 0:
                assert rows == [(ts, vals)]
            else:
                for s, seq in enumerate(sequences):
                    start, end = pair(seq, 4)
                    selected = [0] if nt == 1 else [k for k, t in enumerate(ts) if start <= t <= end]
                    assert rows[s] == ([0] if nt == 1 else [ts[k] - start for k in selected], [vals[k] for k in selected])
                for alias in report['sequenceAliases']:
                    originals = [i for i, s in enumerate(sequences) if unpack(s, 'H')[0] == alias['fallback']]
                    for v, s in enumerate(originals):
                        times, values = rows[s]
                        flags = alias['legacyFlags']
                        length = pair(sequences[s], 4)[1] - pair(sequences[s], 4)[0]
                        expected = (times, values) if flags == 0 else (
                            ([length-t for t in times[::-1]], values[::-1]) if flags == 1 else
                            ([0] if times else [], values[-1:]))
                        assert rows[alias['firstSequence'] + v] == expected
            keys_checked += sum(len(times) for times, _ in rows)
        assert unpack(y, 'f', 172)[0] == unpack(y, 'f', 196)[0] == 0  # new variation fields
        mid = unpack(x, 'f', 332)[0]
        expected_times = [0, math.floor(mid * 32767 + .5), 32767]
        colors = [x[336+k*4:340+k*4] for k in range(3)]
        assert fake(b, y, 260, '3f') == (expected_times, [(float(c[2]), float(c[1]), float(c[0])) for c in colors])
        assert fake(b, y, 276, 'h') == (expected_times, [(math.floor(c[3]*32767/255+.5),) for c in colors])
        scales = unpack(x, '3f', 348)
        assert fake(b, y, 292, '2f') == (expected_times, [(v, v) for v in scales])
        assert y[308:316] == bytes(8)
        for source_offsets, dest in [((360,362,366,368),316), ((372,374,376,378),332)]:
            cells = [unpack(x, 'H', o)[0] for o in source_offsets]
            expected = ([0, expected_times[1], expected_times[1], 32767], [(c,) for c in cells]) if any(cells) else ([], [])
            assert fake(b, y, dest, 'H') == expected
        assert x[380:408] == y[348:376]  # tail/twinkle/inherit/drag
        assert y[376:384] == bytes(8) and x[408:412] == y[384:388] and y[388:392] == bytes(4)
        assert x[448:452] == y[392:396]  # windTime
        assert x[412:448] == y[396:432]  # tumble and wind vectors
        assert x[452:468] == y[432:448]  # follow parameters
    return dict(emitters=len(old), exact_animated_keys=keys_checked)


def check_native(source, converted, native):
    a, b, c = source.read_bytes(), converted.read_bytes(), native.read_bytes()
    assert sha(c) == 'f91b13392c7ba56fd2f1f51c0d2cbff40711094fcad898e0d53ca42f8a8001fb'
    assert c[:8] == b'MD20\x08\x01\0\0' and pair(c, 296)[0] == 10
    for index, (x, y) in enumerate(zip(array(b, 296, 476), array(c, 296, 476))):
        assert x[:24] == y[:24] and x[40:52] == y[40:52]
        for off, fmt in [(260,'3f'), (276,'h'), (292,'2f'), (316,'H'), (332,'H')]:
            tx, vx = fake(b, x, off, fmt)
            ty, vy = fake(c, y, off, fmt)
            assert tx == ty and len(vx) == len(vy)
            assert all(abs(v-w) <= (2e-5 if fmt == '3f' else 0) for u, z in zip(vx, vy) for v, w in zip(u, z))
        assert all(v == w for v, w in zip(unpack(x, '25f', 348), unpack(y, '25f', 348)))
        for j in range(11):
            off = 456 if j == 10 else 52 + j * 20 + (4 if j >= 6 else 0) + (4 if j >= 7 else 0)
            width = 1 if j == 10 else 4
            ours = part_track(b, pair(b, 296)[1] + index * 476 + off, width)
            control = part_track(c, pair(c, 296)[1] + index * 476 + off, width)
            # Blizzard collapses these source endpoint-constant tracks to a singleton;
            # our source-preserving writer keeps both endpoint keys.
            ours_times, ours_values = ours[0]
            control_times, control_values = control[0]
            assert (ours[0] == control[0] or
                    (len(control_values) == 1 and ours_values and
                     all(v == control_values[0] for v in ours_values))), (index, j, ours[0], control[0])
    return dict(sha256=sha(c), emitters=10, static_and_lifetime_tracks='PASS',
                color_float_tolerance=2e-5, source_sha256=sha(a))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=ROOT/'work/elf-map-audit-research/turtle')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-oracle', type=Path)
    parser.add_argument('--dotnet', default=os.environ.get('DOTNET', 'dotnet'))
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT/'work') and not output.exists()
    output.mkdir(parents=True)
    converter = ROOT/'work/toolchains/new-races-model-converter/NewRacesModelConverter.dll'
    def convert(source, target):
        return subprocess.run([args.dotnet, str(converter), 'convert', '--source', str(source),
                               '--output', str(target), '--namespace', r'Character\Custom\HighElfMap\ParticleFixture'],
                              text=True, capture_output=True)
    results = []
    for relative, digest in FIXTURES:
        source = args.source_root/relative
        assert sha(source.read_bytes()) == digest
        for iteration in (1, 2):
            target = output/f'pass{iteration}'/source.stem/(source.stem+'.m2')
            proc = convert(source, target)
            assert proc.returncode == 0, proc.stderr
            geometry = validate(source, target)
            particles = check_particles(source, target)
            report = json.loads(Path(str(target)+'.report.json').read_text())
            assert report['fullySupported'] and not report['unsupportedSemantics']
        first = output/'pass1'/source.stem
        assert {p.name:p.read_bytes() for p in first.iterdir()} == {p.name:p.read_bytes() for p in target.parent.iterdir()}
        assert convert(source, target).returncode != 0
        results.append(dict(source=relative, geometry=geometry, particles=particles, deterministic=True))
        print(source.stem, 'PASS', particles)
    tree = args.source_root/FIXTURES[0][0]
    native = check_native(tree, output/'pass1'/tree.stem/(tree.stem+'.m2'), args.native_oracle) if args.native_oracle else None
    # Exercise real payload encoding beyond the ten static scalar-track source emitters:
    # global lerp, singleton outside clips, nontrivial enable, reverse/freeze fallback,
    # head UVs and nonzero tumble/wind/windTime (never alter the source fixture).
    fixture = bytearray(tree.read_bytes())
    _, particles_offset = pair(fixture, 316)
    def track(emitter, member, times, values, glob=-1):
        header = particles_offset + emitter*504 + member
        pt = len(fixture)
        fixture.extend(struct.pack('<'+'I'*len(times), *times))
        pv = len(fixture)
        fixture.extend(struct.pack('<'+('B' if member == 476 else 'f')*len(values), *values))
        struct.pack_into('<Hh6I', fixture, header, 1 if member != 476 else 0, glob, 0, 0, len(times), pt, len(values), pv)
    gp = len(fixture)
    fixture.extend(struct.pack('<I', 1000))
    struct.pack_into('<II', fixture, 20, 1, gp)
    track(0, 52, [0,500,1000], [-0.0,2.5,7.75], 0)
    track(1, 52, [0], [3.125])
    track(2, 476, [3333,20000], [0,1])
    struct.pack_into('<10f', fixture, particles_offset+412, *[i*.125 for i in range(1,11)])
    _, lookup = pair(fixture, 44)
    struct.pack_into('<H', fixture, lookup+4+2, 1)
    struct.pack_into('<H', fixture, lookup+8+2, 3)
    derived = output/'Derived.m2'
    derived.write_bytes(fixture)
    target = output/'derived'/'Derived.m2'
    proc = convert(derived, target)
    assert proc.returncode == 0, proc.stderr
    derived_result = check_particles(derived, target)
    assert json.loads(Path(str(target)+'.report.json').read_text())['fullySupported']
    print('Derived global/local/enable/UV/spin/wind/fallback fixture PASS')
    rejected = []
    for name, offset, fmt, value in [
        ('repeat', 364, 'H', 2), ('blend-truncation', 40, 'H', 256),
        ('emitter-truncation', 42, 'H', 257), ('spline', 52, 'H', 2),
        ('nonfinite', 408, 'f', float('nan')), ('midpoint', 332, 'f', 0),
        ('midpoint-collapses', 332, 'f', 1e-8),
        ('tail-style', 45, 'B', 1), ('both-style', 45, 'B', 2),
        ('tail-uv', 374, 'H', 1),
        ('global', 54, 'h', 99), ('count', 72, 'I', 3),
        ('offset', 76, 'I', len(fixture)), ('model-resource', 24, 'I', 2),
        ('range', 56, 'I', 3), ('spline-points', 468, 'I', 1),
    ]:
        bad = bytearray(tree.read_bytes())
        struct.pack_into('<'+fmt, bad, particles_offset+offset, value)
        path = output/'rejected'/name/'Source.m2'
        path.parent.mkdir(parents=True)
        path.write_bytes(bad)
        dest = path.with_name('Rejected.m2')
        proc = convert(path, dest)
        assert proc.returncode != 0 and 'Classic particle:' in proc.stderr, (name,proc.stderr)
        assert not dest.exists() and not list(path.parent.glob('*.skin'))
        rejected.append(name)
    summary = dict(schema=1, fixtures=results, native_control=native, derived=derived_result,
                   rejected=rejected, native_runtime='NOT RUN')
    (output/'validation.json').write_text(json.dumps(summary, indent=2)+'\n')
    print('Fail-closed negative fixtures PASS:', len(rejected))
    print(output/'validation.json')


if __name__ == '__main__':
    main()
