#!/usr/bin/env python3
"""Preserve the audited build in the existing server manifest (never install)."""
import sys
sys.dont_write_bytecode = True

import argparse
import json
from pathlib import Path
import shutil

import apply_project_server_data as app
from build_high_elf_server_data import owned_collision, previous_owned


ROOT = Path(__file__).resolve().parent.parent


def stage(build, manifest, recovery=None):
    report_raw = (build / 'report.json').read_bytes()
    report = app.load_json(report_raw)
    intended = app.load_json((build / 'intended-files.json').read_bytes())
    app.require(not report['missing_models'] and not report['collision_conflicts'] and
                not report['vmap_coverage']['stale_installed_tiles'], 'Unresolved build conflicts')
    app.require(intended == {n: r for n, r in report['files'].items()
                            if r['action'] in ('add', 'replace-scoped')}, 'Build plans disagree')
    app.require(report['collision_model_count'] == 2951 and
                 report['counts']['.vmtile'] == 374, 'Unexpected audited build counts')
    app.require(sum(n.endswith('.map') and r['action'] != 'omit-native-unchanged'
                    for n, r in report['files'].items()) == 23 and
                len(report['navigation']['primary']) + len(report['navigation']['halo']) == 43 and
                report['counts']['.mmtile'] == 34, 'Unexpected scoped counts')
    old_digest, _ = app.inventory(manifest)
    document = app.load_json(manifest.read_bytes())
    owned = previous_owned(manifest)
    updating = report.get('previous_manifest_sha256') is not None
    app.require(not updating or report['previous_manifest_sha256'] == old_digest,
                'Previous ownership manifest changed since build')
    files = dict(document['files'])
    by_target = {r['path']: (n, r) for n, r in files.items()}
    by_target.update({r['path']: (n, r) for n, r in files.items()
                      if n == 'high-elf-map/' + r['path']})
    writes = {}

    def preserve(target, raw, kind, accepted=None):
        old = by_target.get(target)
        if old:
            if old[1]['sha256'] == app.sha(raw):
                return
            app.require(old[0] == 'high-elf-map/' + target and updating,
                        'Existing durable source conflict: ' + target)
            if kind != 'additive-dbc':
                kind = 'replace'
                accepted = sorted(set(old[1].get('accepted_before', []) + [old[1]['sha256']]))
        name = 'high-elf-map/' + target
        writes[name] = raw
        files[name] = dict(path=target, size=len(raw), sha256=app.sha(raw), kind=kind)
        if accepted is not None:
            files[name]['accepted_before'] = accepted

    for name, info in report['files'].items():
        if name.startswith('dbc/') or info['action'] == 'omit-native-unchanged':
            continue
        raw = (build / app.canonical(info['source'])).read_bytes()
        app.require(len(raw) == info['size'] and app.sha(raw) == info['sha256'],
                    'Build source drift: ' + name)
        is_model = name.startswith('vmaps/') and Path(name).suffix in ('.m2', '.vmo')
        if is_model:
            if name in owned and owned[name]['sha256'] != info['sha256']:
                app.require(updating and owned_collision(name, info['installed_sha256'], owned),
                            'Unknown previous custom model: ' + name)
            else:
                app.require(info['action'] in ('identical', 'add'), 'Model replacement forbidden')
            preserve(name, raw, 'copy')
        else:
            if updating and name in owned:
                app.require(info['installed_sha256'] in
                            [owned[name]['sha256']] + owned[name].get('accepted_before', []) +
                            [info['sha256'], None], 'Unknown previous scoped payload: ' + name)
            accepted = sorted({info[k] for k in ('installed_sha256', 'native_extraction_sha256')
                               if info.get(k) is not None})
            preserve(name, raw, 'replace' if accepted else 'copy', accepted or None)
    for target in app.ADDITIVE_DBC:
        raw = (ROOT / 'client_patches/archive/source-inputs/high-elf-map/deltas' /
               Path(target).name).read_bytes()
        preserve(target, raw, 'additive-dbc')
    dependencies = {}
    for path, info in app.load_json((build / 'navigation/dependencies.json').read_bytes()).items():
        name = 'maps/' + Path(path).name
        accepted = {info['sha256']}
        recorded = report['files'].get(name)
        # Native-equivalent 33_22 is deliberately omitted; both recorded native
        # encodings are known, rather than replacing the destination's encoding.
        if recorded and recorded['action'] == 'omit-native-unchanged':
            accepted.add(recorded['installed_sha256'])
        dependencies[name] = sorted(accepted)
    contract = dict(
        vmap_tiles=sorted(n for n in report['files'] if n.endswith('.vmtile')),
        mmap_tiles=sorted(n for n in report['files'] if n.endswith('.mmtile')),
        model_closure=sorted(n for n in report['files'] if Path(n).suffix in ('.vmo', '.m2')),
        map_dependencies=dict(sorted(dependencies.items())))
    document = dict(schema=2, files=dict(sorted(files.items())), geography=contract)
    proposed_manifest = app.json_bytes(document)
    if updating and (recovery is not None or writes or proposed_manifest != manifest.read_bytes()):
        app.require(recovery is not None, 'Updated payload requires --recovery outside data/server')
        recovery = recovery.resolve()
        app.require(not recovery.exists() and not recovery.is_relative_to(manifest.parent.resolve()) and
                    not manifest.parent.resolve().is_relative_to(recovery), 'Invalid recovery directory')
        # A complete prior source tree permits inventory/rollback validation, with
        # no extra unlisted recovery files in the active locked tree.
        shutil.copytree(manifest.parent, recovery)
        app.require(app.inventory(recovery / manifest.name)[0] == old_digest,
                    'Recovery inventory mismatch')
    for name, raw in writes.items():
        path = manifest.parent / name
        path.parent.mkdir(parents=True, exist_ok=True)
        app.atomic(path, raw)
    if proposed_manifest != manifest.read_bytes():
        app.atomic(manifest, proposed_manifest)
    digest, payload = app.inventory(manifest)
    print(json.dumps(dict(status='staged', sources=len(files), targets=len(payload),
                         high_elf_sources=sum(n.startswith('high-elf-map/') for n in files),
                         vmap_tiles=len(contract['vmap_tiles']), models=len(contract['model_closure']),
                         deduplicated_models=sum(n in by_target for n in contract['model_closure']),
                         source_bytes=sum(r['size'] for r in files.values()),
                         halo_dependencies=len(dependencies), manifest_sha256=digest,
                          build_report_sha256=app.sha(report_raw)), indent=2))
    return dict(changed_sources=sorted(writes), manifest_sha256=digest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT / 'work/high-elf-server-build')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'data/server/manifest.json')
    parser.add_argument('--recovery', type=Path, help='New directory for the complete previous manifest/source tree')
    args = parser.parse_args()
    stage(args.build, args.manifest, args.recovery)
