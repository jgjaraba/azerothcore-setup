#!/usr/bin/env python3
"""Repair only MMID offsets in revision-1; preserve the collision fix and Z copies."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

from adt_refs import chunk, name_offsets, placed_model_names, remap_name_table
from asset_index import AssetIndex


def run(*args):
    return subprocess.run([str(a) for a in args], check=True, capture_output=True).stdout


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parent.parent
    package = root / 'work/client-overlay-r1'
    baseline = root / 'work/crypt-fix/revision-1/patch-T.MPQ'
    if digest(baseline) != '1455f5576b11c8ea53187488643f37970ec1798ce07483cdebf4c962d57f5229':
        raise ValueError('Unexpected revision-1 archive')
    out = args.output.resolve()
    if out.exists():
        raise ValueError('Use a fresh output directory')
    out.mkdir(parents=True)
    mpq = root / 'tools/mpq'
    index = AssetIndex()
    entries, checks = [], []
    for line in run(mpq, 'list', baseline).decode().splitlines():
        name, size = line.rsplit('\t', 1)
        if name.startswith('('):
            continue
        rel = Path(name.replace('\\', '/'))
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError('Unsafe archive name')
        dest = out / 'payload' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        run(mpq, 'extract-one', baseline, name, dest)
        data = dest.read_bytes()
        if len(data) != int(size):
            raise ValueError('Incomplete extraction')
        if name.lower().endswith('.adt'):
            source = out / ('source-' + rel.name)
            run(mpq, 'extract-one', '/home/dev/wow-turtle/Data/patch-3.mpq', name, source)
            original = source.read_bytes()
            _, old_names = chunk(original, 3, b'XDMM')
            _, old_ids = chunk(original, 4, b'DIMM')
            _, new_names = chunk(data, 3, b'XDMM')
            table_pos, table = chunk(data, 4, b'DIMM')
            if table != old_ids:
                raise ValueError('Unexpected MMID baseline')
            expected = [s[:-4] + b'.m2' if s.lower().endswith(b'.mdx') else s
                        for s in name_offsets(old_names).values()]
            if list(name_offsets(new_names).values()) != expected:
                raise ValueError('Unexpected model-name transformation')
            fixed_ids = remap_name_table(old_names, new_names, old_ids)
            fixed = data[:table_pos] + fixed_ids + data[table_pos+len(table):]
            # Confirm each placement keeps its original slot/model identity.
            before = placed_model_names(original)
            after = placed_model_names(fixed)
            mapped = [s[:-4] + b'.m2' if s.lower().endswith(b'.mdx') else s for s in before]
            if mapped != after:
                raise ValueError('MDDF placement/model identity changed')
            missing = sorted({s.decode('latin1') for s in after
                              if not index.exists(s.decode('latin1'))})
            if missing:
                raise ValueError(f'Unresolved models: {missing}')
            assert data[:table_pos] == fixed[:table_pos]
            assert data[table_pos+len(table):] == fixed[table_pos+len(table):]
            starts = name_offsets(new_names)
            invalid = sum(x[0] not in starts for x in struct.iter_unpack('<I', table))
            dest.write_bytes(fixed)
            checks.append(dict(tile=rel.name, invalid_offsets_before=invalid,
                               mmid_slots=len(table)//4, placements=len(after)))
        entries.append((dest, name))
    assert len(checks) == 6
    manifest = out / 'patch.list'
    manifest.write_text(''.join(f'{p}|{n}\n' for p, n in entries))
    final = out / 'Data/patch-T.MPQ'
    final.parent.mkdir()
    run(mpq, 'create', final, manifest)
    verify = out / 'roundtrip'
    verify.mkdir()
    for i, (path, name) in enumerate(entries):
        result = verify / str(i)
        run(mpq, 'extract-one', final, name, result)
        assert result.read_bytes() == path.read_bytes(), name
    zhashes = {}
    for relative, expected_hash in {
        'Data/patch-Z.mpq': 'cad32e8e64b89c862b857171fa413557c78e11f04aa2274c2d1af19571a3a022',
        'Data/esES/patch-esES-Z.MPQ': '25708c1a31b5532f111222007861e7bd50aad2beff24b40a27d5331c48958b50',
    }.items():
        src, dst = package / relative, out / relative
        assert digest(src) == expected_hash
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        assert digest(dst) == expected_hash
        zhashes[relative] = expected_hash
    report = dict(status='verified', patch_sha256=digest(final), tiles=checks,
                  unchanged_z=zhashes, entries=len(entries), scope='MMID offsets only')
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
