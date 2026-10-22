#!/usr/bin/env python3
"""Preserve verified pilot outputs as repository assets, not a deployment tool.

Uses the validated portable release and accepted coordinated r5 archives as
immutable inputs. Never edits clients, server data, SQL, or existing regular/HD
distributions. Repeating with identical inputs is a no-op; collisions fail.
"""
import argparse
import json
from pathlib import Path

from crypt_release import verify, json_bytes, disjoint
from crypt_release_client import file_sha, sha, require
from apply_project_server_data import inventory

ROOT = Path(__file__).resolve().parent.parent
RELEASE_SHA = 'dd99f86fbe2578857167731034076e3a0d6611fdcc08a3d5ad0413fb97bdb5d2'
R5 = {
    'Data/patch-T.MPQ': '738ef0e3547f2d40ad9e7fbb7ed5608d684bbb51e640b5328b4bf26cce1813ee',
    'Data/patch-Z.mpq': '3b4082bfabc3f02a1efedca81b973548d56f56e32cde6ed4609aa0a2e919d3b0',
    'Data/esES/patch-esES-Z.MPQ': '2de9f73504a6ad457942e8cdc5d9aad55fa663395fda7b4c70f0f3bbec5f19b0',
}


def stage(release, coordinated):
    release, coordinated = Path(release).resolve(), Path(coordinated).resolve()
    server = ROOT / 'data/server'
    client = ROOT / 'client_patches/turtle_crypt'
    for output in (server, client):
        disjoint(output, release, coordinated)
    require(verify(release)['bundle_sha256'] == RELEASE_SHA, 'Unexpected source release')
    source_manifest = json.loads((release / 'manifest.json').read_text())
    outputs, entries = {}, {}
    for name, record in source_manifest['files'].items():
        if not name.startswith('server/'):
            continue
        target = name.removeprefix('server/')
        path = 'turtle-crypt/' + target
        raw = (release / name).read_bytes()
        outputs[server / path] = raw
        entries[path] = dict(path=target, size=len(raw), sha256=sha(raw),
                             kind='dbc-delta' if target.startswith('dbc/') else 'copy')
    require(len(entries) == 430, 'Expected complete server payload')
    outputs[server / 'manifest.json'] = json_bytes(dict(schema=1, files=entries))
    client_files = {}
    for name, expected in R5.items():
        require(file_sha(coordinated / name) == expected, f'Wrong coordinated source: {name}')
        path = 'r5-coordinated/' + name
        raw = (coordinated / name).read_bytes()
        outputs[client / path] = raw
        client_files[path] = sha(raw)
    for name in ('Data/patch-T.MPQ', 'report.json'):
        raw = (release / 'client' / name).read_bytes()
        path = 'stock-esES/' + name
        outputs[client / path] = raw
        client_files[path] = sha(raw)
    outputs[client / 'SHA256SUMS'] = ''.join(
        f'{digest}  {name}\n' for name, digest in sorted(client_files.items())).encode()
    # Validate the entire intended write set before preserving anything.
    for path, raw in outputs.items():
        require(not any(p.is_symlink() for p in (path, *path.parents)), f'Symlink output: {path}')
        require(not path.exists() or path.is_file() and path.read_bytes() == raw,
                f'Repository asset collision: {path}')
    for path, raw in outputs.items():
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    digest, payload = inventory(server / 'manifest.json')
    return dict(status='PASS', server_files=len(payload), server_manifest_sha256=digest,
                client_files=client_files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--coordinated', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(stage(args.release, args.coordinated), indent=2, sort_keys=True))
