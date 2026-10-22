#!/usr/bin/env python3
"""Clean-client-only portable crypt release builder. No client writes.

Archive order is always declared low-to-high in a JSON array of paths relative
to Data. extract-baseline reads only that stock subset (even from a dirty source
snapshot); build --client additionally requires a clean Data tree. Fixtures are
extracted resource directories with baseline.json provenance, not stock proof.
Stock authenticity is operator-declared; exact hashes bind target installations
to that declared baseline, rather than certifying an official Blizzard release.
Only the immutable accepted r5 T supplies pilot art and row deltas.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from crypt_release_dbc import merge_dbc, parse_dbc

ROOT = Path(__file__).resolve().parent.parent
R5_SHA256 = '738ef0e3547f2d40ad9e7fbb7ed5608d684bbb51e640b5328b4bf26cce1813ee'
TRS = r'Textures\Minimap\md5translate.trs'
# name: field count, selected IDs, every string-offset field, map ordering
DBC_DELTAS = {
    'Map.dbc': (66, [800], [1, *range(5, 21), *range(23, 39), *range(40, 56)], False),
    'AreaTable.dbc': (36, [5086], list(range(11, 27)), False),
    'MapDifficulty.dbc': (23, [756], list(range(3, 19)), False),
    'WorldMapArea.dbc': (11, [674], [3], False),
    'LoadingScreens.dbc': (4, [511], [1, 2], False),
    'AreaTrigger.dbc': (10, [900800, 900801], [], True),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def key(name):
    return name.replace('/', '\\').lower()


def relative(name):
    parts = name.replace('\\', '/').split('/')
    require(all(p and p not in ('.', '..') and ':' not in p for p in parts)
            and not any(ord(c) < 32 or c == '|' for c in name), 'Unsafe resource path')
    return Path(*parts)


def resources():
    return [rf'DBFilesClient\{name}' for name in DBC_DELTAS] + [TRS]


def mpq_run(tool, *args):
    return subprocess.run([str(tool), *map(str, args)], capture_output=True, check=True)


def extract(tool, archive, name, optional=False):
    with tempfile.TemporaryDirectory(prefix='crypt-mpq-') as tmp:
        path = Path(tmp) / 'member'
        proc = subprocess.run([str(tool), 'extract-one', str(archive), name, str(path)],
                              capture_output=True)
        if proc.returncode:
            if optional and proc.stderr.strip() == b'ERROR: file not found in archive':
                return None
            raise ValueError(f'MPQ extraction failed: {archive}: {name}: {proc.stderr.decode()}')
        return path.read_bytes()


def members(tool, archive):
    proc = mpq_run(tool, 'list', archive)
    result = {}
    for line in proc.stdout.decode().splitlines():
        name, size = line.rsplit('\t', 1)
        require(not re.fullmatch(r'File[0-9a-fA-F]+\..*', name), 'Unresolved MPQ member')
        if name == '(listfile)':
            continue
        relative(name)
        require(not name.startswith('(') and key(name) not in result, 'Unsupported/duplicate MPQ entry')
        data = extract(tool, archive, name)
        require(len(data) == int(size), 'Short MPQ extraction')
        result[key(name)] = (name, data)
    counts = re.search(rb'# archive files: (\d+)', proc.stderr)
    require(counts and int(counts[1]) == len(result) + 1, 'Incomplete MPQ listing')
    return result


def parse_trs(raw):
    entries = {}
    for line in raw.decode('ascii').splitlines():
        if not line.strip() or line.lower().startswith('dir: '):
            continue
        parts = line.split('\t')
        require(len(parts) == 2, 'Invalid TRS line')
        name, value = parts
        relative(name)
        relative(value)
        require(name.lower().endswith('.blp') and value.lower().endswith('.blp'), 'Invalid TRS path')
        require(key(name) not in entries, 'Duplicate TRS key')
        entries[key(name)] = (name, value)
    return entries


def pilot_trs(donor):
    entries = parse_trs(donor)
    result = [pair for name, pair in entries.items() if name.startswith(
        ('karazhancrypt\\', 'wmo\\custom\\turtle800\\tw800crypt_'))]
    require(len(result) == 29, 'Expected exactly 29 pilot TRS additions')
    return sorted(result, key=lambda pair: key(pair[0]))


def merge_trs(base, donor):
    existing = parse_trs(base)
    additions = []
    for name, value in pilot_trs(donor):
        if key(name) in existing:
            require(key(existing[key(name)][1]) == key(value), f'TRS collision: {name}')
        else:
            additions.append((name, value))
    if not additions:
        return base
    newline = b'\r\n' if b'\r\n' in base else b'\n'
    suffix = []
    for name, value in additions:
        suffix.extend(['dir: ' + name.rsplit('\\', 1)[0], name + '\t' + value])
    return base + (b'' if not base or base.endswith(b'\n') else newline) + newline.join(
        s.encode('ascii') for s in suffix) + newline


def stock_path(name):
    """Only original 3.3.5 archive names; custom patches never become clean."""
    path = relative(name)
    parts = [p.lower() for p in path.parts]
    if len(parts) == 1:
        return bool(re.fullmatch(r'(common(-2)?|expansion|lichking|patch(-[23])?)\.mpq', parts[0]))
    if len(parts) != 2 or not re.fullmatch(r'[a-z]{4}', parts[0]):
        return False
    locale = parts[0]
    return bool(re.fullmatch(
        rf'((base|backup|locale|speech|expansion-locale|expansion-speech|lichking-locale|lichking-speech)-{locale}|patch-{locale}(-[23])?)\.mpq', parts[1]))


def archive_records(root, archives):
    require(isinstance(archives, list) and archives, 'Declare ordered archive list (low to high)')
    seen, records = set(), []
    for name in archives:
        require(isinstance(name, str) and stock_path(name), f'Non-stock archive: {name}')
        canonical = key(name)
        require(canonical not in seen, 'Duplicate archive declaration')
        seen.add(canonical)
        path = root / 'Data' / relative(name)
        require(path.is_file() and not path.is_symlink(), f'Missing/symlink archive: {path}')
        require(path.resolve().is_relative_to(root.resolve()), 'Archive escapes client root')
        records.append(dict(path=relative(name).as_posix(), sha256=file_sha(path), size=path.stat().st_size))
    return records


def preflight_client(client, manifest):
    """Read-only exact archive set/hash guard; reject loose resource overrides."""
    client = Path(client)
    require((client / 'Data').is_dir() and not (client / 'Data').is_symlink(), 'Missing/symlink Data')
    for path in client.iterdir():
        require(path.name.lower() not in ('dbfilesclient', 'world', 'textures', 'interface'),
                f'Loose client resource directory: {path.name}')
    expected = {r['path']: r for r in manifest['archives']}
    found = {}
    for path in (client / 'Data').rglob('*'):
        require(not path.is_symlink(), f'Symlink in Data: {path}')
        if not path.is_file():
            continue
        name = path.relative_to(client / 'Data').as_posix()
        if path.suffix.lower() == '.mpq':
            require(stock_path(name), f'Unknown custom patch: {name}')
            found[name] = path
        else:
            # Original locale documentation/config cannot override game resources.
            require(path.suffix.lower() in ('.html', '.url', '.wtf') and
                    not any(p.lower() in ('dbfilesclient', 'world', 'textures', 'interface')
                            for p in path.relative_to(client / 'Data').parts),
                    f'Loose Data file: {name}')
    require(set(found) == set(expected), 'Client archive set differs from declared clean baseline')
    for name, path in found.items():
        require(path.stat().st_size == expected[name]['size'] and
                file_sha(path) == expected[name]['sha256'], f'Client archive hash mismatch: {name}')
    require(found, 'Missing client Data archives')
    return dict(status='PASS', archives=len(found))


def read_archive_baseline(client, archives, tool):
    """Explicit stock-subset extraction; does not certify source directory clean."""
    records = archive_records(Path(client), archives)
    baseline, origins = {}, {}
    for record in records:
        archive = Path(client) / 'Data' / record['path']
        for name in resources():
            raw = extract(tool, archive, name, optional=True)
            if raw is not None:
                baseline[key(name)] = raw
                origins[key(name)] = record['path']
    require(set(baseline) == {key(n) for n in resources()}, 'Missing stock baseline resources')
    require(archive_records(Path(client), archives) == records, 'Input archive drift')
    return baseline, dict(schema=1, archives=records, order='low-to-high; explicit',
        resources={name: dict(sha256=sha(raw), archive=origins[name]) for name, raw in baseline.items()})


def write_fixture(output, baseline, manifest):
    output = Path(output)
    require(not output.exists(), 'Output must be fresh')
    output.mkdir(parents=True)
    for name, raw in baseline.items():
        path = output / relative(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    (output / 'baseline.json').write_text(json.dumps(manifest, indent=2) + '\n')


def read_fixture(path):
    path = Path(path)
    manifest = json.loads((path / 'baseline.json').read_text())
    baseline = {key(name): (path / relative(key(name))).read_bytes() for name in resources()}
    for name, raw in baseline.items():
        require(sha(raw) == manifest['resources'][name]['sha256'], f'Fixture hash mismatch: {name}')
    require(manifest['archives'] and all(stock_path(r['path']) for r in manifest['archives']),
            'Fixture must declare stock archive provenance')
    return baseline, manifest


def build_client(pilot, output, *, baseline=None, client=None, archives=None, tool=ROOT / 'tools/mpq'):
    """Build fresh local artifact; returns JSON-serializable manifest.

    baseline: extracted fixture path; OR client + archives: clean installation
    and explicit low-to-high list relative to Data. No automatic load ordering.
    """
    pilot, output, tool = Path(pilot).resolve(), Path(output).resolve(), Path(tool).resolve()
    require(not output.exists(), 'Output must be fresh')
    inputs = [pilot, tool] + ([Path(baseline).resolve()] if baseline else [Path(client).resolve()] if client else [])
    require(all(not output.is_relative_to(p) and not p.is_relative_to(output) for p in inputs),
            'Output overlaps inputs')
    require(file_sha(pilot) == R5_SHA256, 'Pilot must be immutable accepted r5 T')
    require(bool(baseline) != bool(client), 'Choose fixture baseline or clean client')
    if baseline:
        base, source = read_fixture(baseline)
    else:
        records = archive_records(Path(client), archives)
        preflight_client(client, dict(archives=records))
        base, source = read_archive_baseline(client, archives, tool)
    donor = members(tool, pilot)
    actual_dbcs = {n for n in donor if n.endswith('.dbc')}
    require(actual_dbcs == {key(n) for n in resources() if n.endswith('.dbc')},
            'Unexpected pilot DBC inventory')
    require(len(donor) == 71, 'Unexpected r5 pilot inventory')
    payload, changes = {}, {}
    for canonical, (name, raw) in donor.items():
        if canonical in base:
            original = base[canonical]
            if canonical == key(TRS):
                merged = merge_trs(original, raw)
            else:
                fields, ids, strings, order = DBC_DELTAS[relative(name).name]
                require(parse_dbc(original)[0] == fields, f'Unexpected stock schema: {name}')
                merged = merge_dbc(original, raw, ids, strings, order)
            payload[canonical] = (name, merged)
            changes[canonical] = dict(original_sha256=sha(original), donor_sha256=sha(raw),
                                      generated_sha256=sha(merged))
        else:
            payload[canonical] = (name, raw)
    require(file_sha(pilot) == R5_SHA256, 'Pilot changed during read')
    output.mkdir(parents=True)
    stage = output / 'payload'
    stage.mkdir()
    lines, inventory = [], []
    for i, (canonical, (name, raw)) in enumerate(sorted(payload.items())):
        path = stage / str(i)
        path.write_bytes(raw)
        os.utime(path, (0, 0))
        lines.append(f'{path}|{name}\n')
        inventory.append(dict(member=name, sha256=sha(raw), size=len(raw),
                              pilot_byteexact=canonical not in changes))
    listing = output / 'members.list'
    listing.write_text(''.join(lines))
    artifact = output / 'Data/patch-T.MPQ'
    artifact.parent.mkdir()
    mpq_run(tool, 'create', artifact, listing)
    require(members(tool, artifact) == payload, 'MPQ roundtrip mismatch')
    # Re-read fixture/client hashes after packaging, not merely at discovery.
    if baseline:
        require(read_fixture(baseline) == (base, source), 'Fixture changed during build')
    else:
        preflight_client(client, source)
    require(file_sha(pilot) == R5_SHA256, 'Pilot drift')
    report = dict(schema=1, kind='crypt-clean-client', status='byte-validated; not installed',
        pilot_sha256=R5_SHA256, baseline=source, target_preflight=dict(archives=source['archives'],
            reject_extra_mpqs=True, reject_loose_resources=True),
        artifact=dict(path='Data/patch-T.MPQ', sha256=file_sha(artifact), size=artifact.stat().st_size),
        generated_resources=changes, inventory=inventory, pilot_trs_additions=29,
        dbc_tables=len(DBC_DELTAS), mpq_tool_sha256=file_sha(tool))
    (output / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mpq', type=Path, default=ROOT / 'tools/mpq')
    commands = parser.add_subparsers(dest='command', required=True)
    fixture = commands.add_parser('extract-baseline', help='Extract a declared stock subset read-only')
    fixture.add_argument('--archive-root', type=Path, required=True)
    fixture.add_argument('--archives', type=Path, required=True, help='JSON array, low to high, relative to Data')
    fixture.add_argument('--output', type=Path, required=True)
    build = commands.add_parser('build')
    build.add_argument('--pilot', type=Path, required=True)
    group = build.add_mutually_exclusive_group(required=True)
    group.add_argument('--baseline', type=Path)
    group.add_argument('--client', type=Path)
    build.add_argument('--archives', type=Path, help='Required with --client; explicit JSON order')
    build.add_argument('--output', type=Path, required=True)
    check = commands.add_parser('preflight')
    check.add_argument('--client', type=Path, required=True)
    check.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'extract-baseline':
            root, out = args.archive_root.resolve(), args.output.resolve()
            require(not out.is_relative_to(root) and not root.is_relative_to(out), 'Output overlaps source')
            base, manifest = read_archive_baseline(root, json.loads(args.archives.read_text()), args.mpq)
            write_fixture(out, base, manifest)
            result = dict(baseline=str(out), resources=len(base))
        elif args.command == 'build':
            result = build_client(args.pilot, args.output, baseline=args.baseline, client=args.client,
                archives=json.loads(args.archives.read_text()) if args.archives else None, tool=args.mpq)
        else:
            report = json.loads(args.report.read_text())
            result = preflight_client(args.client, report['target_preflight'])
        if args.command == 'build':
            result = dict(artifact=result['artifact'], report=str(args.output / 'report.json'))
        print(json.dumps(result, indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'ERROR: {exc}\n')


if __name__ == '__main__':
    main()
