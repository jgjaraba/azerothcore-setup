#!/usr/bin/env python3
"""Build an isolated map-800 collision fix from the clients and pilot MPQ.

Only writes under --output. Does not install into clients or server runtime.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

import crypt_collision_fix as collision
from dbc import read_dbc

OLD = b"world\\wmo\\dungeon\\md_crypt\\md_crypt_d.wmo"
NEW = b"World\\wmo\\Custom\\Turtle800\\tw800crypt.wmo"


def run(*args):
    return subprocess.run([str(a) for a in args], check=True, capture_output=True).stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parent.parent
    mpq = root / 'tools/mpq'
    out = args.output.resolve()
    if out.exists():
        raise ValueError('Use a fresh output directory; existing artifacts are preserved')
    out.mkdir(parents=True)
    sources = out / 'sources'
    sources.mkdir()
    # Re-extract pinned inputs; never depend on temporary research files.
    for i, _ in enumerate(collision.SOURCE_SHA256):
        suffix = '' if i == 0 else f'_{i-1:03}'
        run(mpq, 'extract-one', '/home/dev/wow-335/Data/common-2.MPQ',
            'World\\wmo\\Dungeon\\MD_Crypt\\MD_Crypt_D' + suffix + '.wmo',
            sources / (collision.SOURCE_PREFIX + suffix + '.wmo'))
    run(mpq, 'extract-one', '/home/dev/wow-turtle/Data/wmo.MPQ',
        'World\\wmo\\Dungeon\\MD_Crypt\\MD_Crypt_D_000.wmo',
        sources / collision.TURTLE_NAME)
    run('python3', root / 'tools/crypt_collision_fix.py', '--source-dir', sources,
        '--output-dir', out / 'wmo')
    listing = run(mpq, 'list', args.base.resolve()).decode().splitlines()
    entries = []
    changed = []
    for line in listing:
        name, size = line.rsplit('\t', 1)
        if name.startswith('('):
            continue
        relative = Path(name.replace('\\', '/'))
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe archive path')
        dest = out / 'payload' / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        run(mpq, 'extract-one', args.base.resolve(), name, dest)
        data = dest.read_bytes()
        if len(data) != int(size):
            raise ValueError('Incomplete extraction')
        if name.lower().endswith('.adt'):
            # Equal-length replacement: preserve MWID and every other offset.
            assert len(OLD) == len(NEW)
            mhdr = struct.unpack_from('<16I', data, 20)
            mwmo = 20 + mhdr[5]
            assert data[mwmo:mwmo+4] == b'OMWM'
            end = mwmo + 8 + struct.unpack_from('<I', data, mwmo+4)[0]
            body = data[mwmo+8:end]
            names = body.split(b'\0')
            replaced = 0
            for i, item in enumerate(names):
                if item.lower() == OLD:
                    names[i] = NEW
                    replaced += 1
            if replaced:
                assert replaced == 1
                new_data = data[:mwmo+8] + b'\0'.join(names) + data[end:]
                assert len(new_data) == len(data)
                dest.write_bytes(new_data)
                changed.append(name)
        entries.append((dest, name))
    assert len(changed) == 4, changed
    _, rows, _ = read_dbc(str(out / 'payload/DBFilesClient/MapDifficulty.dbc'))
    assert any(r[0:3] == (756, 800, 0) for r in rows)
    family = out / 'wmo/World/wmo/Custom/Turtle800'
    for path in sorted(family.glob('*.wmo')):
        entries.append((path, 'World\\wmo\\Custom\\Turtle800\\' + path.name))
    assert len(list(family.glob('*.wmo'))) == 20
    manifest = out / 'patch.list'
    manifest.write_text(''.join(f'{p}|{n}\n' for p, n in entries))
    archive = out / 'patch-T.MPQ'
    run(mpq, 'create', archive, manifest)
    # Round-trip every entry through the actual archive reader.
    check = out / 'roundtrip'
    check.mkdir()
    for i, (path, name) in enumerate(entries):
        dest = check / str(i)
        run(mpq, 'extract-one', archive, name, dest)
        assert dest.read_bytes() == path.read_bytes(), name
    report = dict(base=str(args.base.resolve()), changed_adts=changed,
                  entries=len(entries), sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
    (out / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
