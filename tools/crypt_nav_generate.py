#!/usr/bin/env python3
"""Generate an isolated map800 navigation candidate; never install it.

Keep all native voxel/clearance parameters explicit. Only the requested tile
simplification error changes. Source maps/vmaps are read-only generator inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tile_info(path):
    data = path.read_bytes()
    magic, version, mmap_version, size = struct.unpack_from('<4I', data)
    if magic != 0x4d4d4150 or mmap_version != 20 or len(data) != 56+size:
        raise ValueError(f'Invalid mmap tile: {path}')
    header = struct.unpack_from('<15i', data, 56)
    if header[0] != 0x444e4156 or header[1] != version:
        raise ValueError('Invalid Detour header')
    return dict(file=path.name, sha256=sha(path), size=len(data),
                poly_count=header[6], vertex_count=header[7],
                detail_vertices=header[10], detail_triangles=header[11],
                simplification_error=struct.unpack_from('<f', data, 52)[0])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--error', type=float, default=0.9)
    ap.add_argument('--all-tiles', action='store_true')
    args = ap.parse_args()
    if args.output.exists() or not 0.8 <= args.error <= 2:
        raise ValueError('Use a fresh output directory and error in [0.8,2]')
    root = Path(__file__).resolve().parent.parent
    geometry = root / 'work/server-data/crypt-refs-r2'
    source_maps, source_vmaps = (geometry / 'maps').resolve(), geometry / 'vmaps'
    if not source_maps.is_dir() or not source_vmaps.is_dir():
        raise ValueError('Missing verified pilot geometry')
    generator = Path('/home/dev/azerothcore/env/dist/bin/mmaps_generator')
    out = args.output.resolve()
    out.mkdir(parents=True)
    (out / 'maps').symlink_to(source_maps, target_is_directory=True)
    (out / 'vmaps').symlink_to(source_vmaps, target_is_directory=True)
    (out / 'mmaps').mkdir()
    (out / 'meshes').mkdir()
    if '"' in str(out) or '\n' in str(out) or '\\' in str(out):
        raise ValueError('Output path cannot be represented safely in the YAML template')
    template = (root / 'tools/crypt-nav-800.yaml.in').read_text()
    if template.count('@DATA_DIR@') != 1 or template.count('@ERROR@') != 1:
        raise ValueError('Unexpected profile template')
    config = template.replace('@DATA_DIR@', str(out)).replace('@ERROR@', str(args.error))
    cfg = out / 'mmaps-800.yaml'
    cfg.write_text(config)
    command = [str(generator), '800', '--config', str(cfg), '--threads', '1', '--silent']
    if not args.all_tiles:
        command += ['--tile', '35,52']
    inputs = {str(p):sha(p) for p in sorted(source_maps.glob('800*.map'))}
    inputs.update({str(p):sha(p) for p in sorted(source_vmaps.iterdir()) if p.is_file()})
    with (out / 'generator.log').open('wb') as log:
        result = subprocess.run(command, cwd=out, stdout=log, stderr=subprocess.STDOUT)
    for p, expected in inputs.items():
        if sha(Path(p)) != expected:
            raise ValueError(f'Geometry input changed: {p}')
    tiles = [tile_info(p) for p in sorted((out/'mmaps').glob('800*.mmtile'))]
    report = dict(command=command, exit_code=result.returncode,
                  generator_sha256=sha(generator), config_sha256=sha(cfg),
                  geometry_sha256=inputs, tiles=tiles,
                  tile_35_52_generated=(out/'mmaps/8005235.mmtile').is_file(),
                  note='Exit code alone is not a successful-navigation test')
    (out / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'geometry_sha256'}, indent=2))


if __name__ == '__main__':
    main()
