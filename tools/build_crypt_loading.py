#!/usr/bin/env python3
"""Stage r5 client-only loading screen. Stdlib + existing StormLib MPQ CLI.

All inputs are opened read-only. Output must be fresh and under setup/work.
No research /tmp inputs, database access or runtime operations are used.
"""
import argparse
import json
from pathlib import Path
import struct

from build_crypt_cartography import Builder, ROOT, file_sha, normalize, require, sha

MAP = r'DBFilesClient\Map.dbc'
LOADING = r'DBFilesClient\LoadingScreens.dbc'
ART = r'Interface\Glues\LoadingScreens\LoadScreenKarazhanCrypt.blp'
BASE = ROOT / 'work/client-overlay-r4.1'
BASE_HASHES = {
    'Data/patch-T.MPQ': '0c6e851df5961c0062ba47b617b25078c29b67dacf7278d1b77a259ab031a681',
    'Data/patch-Z.mpq': 'cad32e8e64b89c862b857171fa413557c78e11f04aa2274c2d1af19571a3a022',
    'Data/esES/patch-esES-Z.MPQ': '25708c1a31b5532f111222007861e7bd50aad2beff24b40a27d5331c48958b50',
}
NATIVE_HASH = '8640ce1430c37182794ed331cbcc6fb890a0b22eb9616681503ba1a4ac9e4ac4'
ART_HASH = '1c0de23be00e87706286616e72c74a035986ee7ff0b31a7fb49a2a39926ddcbd'
OLD_ART_HASH = '7e908261254ef6a04f4cd14689395e6caa0f19d55656bd4a86f44f31e8b420b6'
# Pinned table versions from the researched reference snapshot. Archive hashes
# (including archives with no matching member) are recorded in each report.
KNOWN_TABLES = {
    MAP: set('''059ea21a2c82cff17faced5db841de056c83f6bd5664cd19a51df3676347fce7
0f2e0636d9966e8a271ec1610c9f6518430a17f8bb9aa0809c443004b9bb66dc
1b03f51f50a73eea8bd6f66b5ad60dd673ab7203b218324bfc504147a03e30d3
1e7aecbd06aa3a4d48397da5e5b036fe0dc71c134f3738bb9778912aabe3b888
261bd7c2c9dbdba1f2966ca21106673ed722c2e3681d227f1eed261b6ce870d5
47c15577033f58b5f2eee68235d47be29201b0ee1bcb138965400f3cd8ddfc31
a6ad63267b5a2d34032779c257aeaa27be34f277e14efe3d98fb8786c1237b49
b9b4c57837a0d6e5167fdfae08cb0efd9ca6e18afbedc6fb3682eb9afcba4a40
bfe0424a2ef770368b8261b0eacd930c9dde0df0875c82698ba2f77f353e7bfb
fa24da745932677ff106368157ea857ec48ed3d42fdef8e70fa7dca7223ddaca'''.split()),
    LOADING: {NATIVE_HASH,
        'b658b8c05f320ba48a60aef098076b0039c8d2f6ba06a721c06149a2dadb6b89',
        'c5e7c339d24d66ee46ac0fb0f968aca5450e048a531b0611591c9d40aaf29152',
        'd36744757bb4df816cf7f9014eac137c21e12ac22e67fb1b96595e1fbda1b7dd'},
}


def table(raw, fields):
    require(len(raw) >= 20 and raw[:4] == b'WDBC', 'Invalid WDBC')
    n, f, size, ns = struct.unpack_from('<4I', raw, 4)
    require(f == fields and size == 4*f and len(raw) == 20+n*size+ns,
            'Unexpected DBC layout')
    rows = [struct.unpack_from('<' + 'I'*f, raw, 20+i*size) for i in range(n)]
    require(len({r[0] for r in rows}) == n, 'Duplicate DBC IDs')
    return rows, raw[20+n*size:]


def string(block, offset):
    require(offset < len(block) and b'\0' in block[offset:], 'Invalid string offset')
    return block[offset:block.index(b'\0', offset)].decode('utf-8')


def append_loading(raw, name, path):
    rows, strings = table(raw, 4)
    require(len(rows) == 91 and max(r[0] for r in rows) == 254,
            'Unexpected native loading records')
    require(511 not in {r[0] for r in rows}, 'Loading ID collision')
    extra = name.encode() + b'\0' + path.encode() + b'\0'
    row = (511, len(strings), len(strings)+len(name.encode())+1, 0)
    # Preserve physical order even if the native table is not ID sorted.
    result = (struct.pack('<4s4I', b'WDBC', 92, 4, 16, len(strings)+len(extra))
              + raw[20:20+91*16] + struct.pack('<4I', *row) + strings + extra)
    actual, block = table(result, 4)
    require(actual[:-1] == rows and block[:len(strings)] == strings, 'Native loading data changed')
    return result, dict(id=511, name=name, filename=path, has_wide_screen=0,
                        raw_row=row, rows_before=91, rows_after=92,
                        native_id_order_ascending=[r[0] for r in rows] == sorted(r[0] for r in rows),
                        native_records_and_strings_byteexact=True)


def update_map(raw):
    rows, _ = table(raw, 66)
    require(len(rows) == 136, 'Unexpected baseline Map count')
    require(not any(r[57] == 511 for r in rows), 'Map loading reference collision')
    matches = [(i, r) for i, r in enumerate(rows) if r[0] == 800]
    require(len(matches) == 1 and matches[0][1][57] == 0, 'Unexpected Map800 loading')
    i, row = matches[0]
    offset = 20+i*264+57*4
    result = raw[:offset] + struct.pack('<I', 511) + raw[offset+4:]
    return result, dict(id=800, field_index=57, before=0, after=511,
                        row_before=row, row_after=table(result, 66)[0][i],
                        all_other_bytes_preserved=True)


def normalize_blp(raw):
    """Clear only nonexistent mip descriptors; never recompress/convert art."""
    require(len(raw) >= 1172 and raw[:4] == b'BLP2', 'Invalid BLP2')
    require(struct.unpack_from('<I4B2I', raw, 4) == (1, 2, 0, 0, 1, 512, 512),
            'Unexpected BLP family')
    offsets = struct.unpack_from('<16I', raw, 20)
    sizes = struct.unpack_from('<16I', raw, 84)
    ranges = []
    for level in range(10):  # log2(512)+1: levels 0 through 9 only
        w = max(1, 512 >> level)
        expected = ((w+3)//4)**2*8
        start, size = offsets[level], sizes[level]
        require(size == expected, 'Invalid active DXT1 size')
        require(start >= 1172 and start+size <= len(raw), 'Invalid active mip range')
        require(all(start+size <= a or start >= b for a, b in ranges), 'Overlapping active mips')
        ranges.append((start, start+size))
    result = bytearray(raw)
    for level in range(10, 16):
        struct.pack_into('<I', result, 20+level*4, 0)
        struct.pack_into('<I', result, 84+level*4, 0)
    result = bytes(result)
    require(result[148:] == raw[148:] and result[:60] == raw[:60]
            and result[84:124] == raw[84:124], 'Art bytes changed')
    return result, dict(source_sha256=sha(raw), normalized_sha256=sha(result),
        active_levels=10, active_ranges=ranges, source_offsets=offsets, source_sizes=sizes,
        unused_levels_cleared=list(range(10, 16)), palette_and_entire_payload_byteexact=True,
        reason='Invalid nonexistent mip-tail pointers; metadata fix only, no art conversion')


class LoadingBuilder(Builder):
    def pinned(self, archive, name, digest):
        raw = self.extract(archive, name)
        require(sha(raw) == digest, f'Pinned input mismatch: {archive}: {name}')
        return raw

    def members(self, archive):
        result = {}
        for line in self.run('list', archive).decode().splitlines():
            name, size = line.rsplit('\t', 1)
            key = normalize(name)
            require(key not in result and not name.startswith('File'), 'Unresolved/duplicate member')
            data = self.extract(archive, name)
            require(len(data) == int(size), 'Short member extraction')
            result[key] = (name, data)
        require(all(not n.startswith('(') or n == '(listfile)' for n in result),
                'Unresearched internal metadata')
        return result

    def build(self):
        for relative, digest in BASE_HASHES.items():
            require(file_sha(BASE / relative) == digest, 'Approved baseline mismatch')
        turtle = self.turtle / 'Data/patch-9.mpq'
        source = self.pinned(turtle, LOADING,
            'd71444756b6ed3ccef45a703181c29b5c535643aee1a6edb7d1a906b7b4a6fc0')
        rows, block = table(source, 3)
        row = next(r for r in rows if r[0] == 511)
        name, path = string(block, row[1]), string(block, row[2])
        require(name == 'Karazhan Crypt' and path == ART, 'Unexpected Turtle row511')
        source_map = self.pinned(turtle, MAP,
            '812bb8b30244aedf776199469163a7c3f75da890f05f678fc7b2776d7399df72')
        require(next(r for r in table(source_map, 42)[0] if r[0] == 800)[38] == 511,
                'Turtle Map loading provenance mismatch')
        art, art_info = normalize_blp(self.pinned(self.turtle / 'Data/patch-4.mpq', ART, ART_HASH))
        turtle_art_audit = []
        wide = ART[:-4] + 'Wide.blp'
        for number in range(9, 3, -1):
            archive = self.turtle / f'Data/patch-{number}.mpq'
            if not archive.exists():
                continue
            candidate = self.extract(archive, ART, optional=True)
            require(candidate is None or (number == 4 and sha(candidate) == ART_HASH),
                    'Unexpected higher-priority Turtle art')
            require(self.extract(archive, wide, optional=True) is None, 'Unexpected wide asset')
            turtle_art_audit.append(dict(archive=str(archive), art_sha256=sha(candidate) if candidate else None,
                                         wide_asset_present=False))
        native = self.pinned(self.w335 / 'Data/enUS/patch-enUS-3.MPQ', LOADING, NATIVE_HASH)
        merged, loading_info = append_loading(native, name, path)
        audit = []
        snapshots = sorted(p for p in (self.w335 / 'Data').rglob('*')
                           if p.is_file() and p.suffix.lower() == '.mpq')
        require(snapshots, 'Missing snapshot archives')
        for archive in snapshots:
            hits = {}
            for member, fields in ((MAP, 66), (LOADING, 4)):
                raw = self.extract(archive, member, optional=True)
                hits[member] = sha(raw) if raw is not None else None
                if raw is not None:
                    require(sha(raw) in KNOWN_TABLES[member], f'Unknown snapshot table: {archive}/{member}')
                    actual_fields = struct.unpack_from('<I', raw, 8)[0]
                    if member == MAP:
                        require(actual_fields in (65, 66, 126), 'Unknown historical Map layout')
                        reference_field = 62 if actual_fields == 126 else 57
                    else:
                        require(actual_fields in (3, 4), 'Unknown LoadingScreens layout')
                        reference_field = 0
                    records, _ = table(raw, actual_fields)
                    require(not any(r[reference_field] == 511 for r in records),
                            f'Snapshot ID/reference collision: {archive}')
            old_art = self.extract(archive, ART, optional=True)
            require(old_art is None or sha(old_art) == OLD_ART_HASH, 'Unknown snapshot art override')
            require(self.extract(archive, wide, optional=True) is None, 'Unexpected snapshot wide asset')
            hits[ART] = sha(old_art) if old_art is not None else None
            audit.append(dict(archive=str(archive), members=hits))
        outputs = {}
        for index, relative in enumerate(BASE_HASHES):
            source_archive = BASE / relative
            before = self.members(source_archive)
            resources = {k: v for k, v in before.items() if k != '(listfile)'}
            require(normalize(LOADING) not in resources, 'Unexpected baseline LoadingScreens override')
            require(normalize(wide) not in resources, 'Unexpected baseline wide asset')
            map_key, art_key = normalize(MAP), normalize(ART)
            changed_map, map_info = update_map(resources[map_key][1])
            after = dict(resources)
            after[map_key] = (resources[map_key][0], changed_map)
            if index == 0:
                require(len(resources) == 69 and art_key not in resources, 'Unexpected T resources')
                after[normalize(LOADING)] = (LOADING, merged)
                after[art_key] = (ART, art)
            elif art_key in resources:
                require(sha(resources[art_key][1]) == OLD_ART_HASH, 'Unexpected baseline art')
                after[art_key] = (resources[art_key][0], art)
            require(index != 1 or art_key in resources, 'Missing old root Z art')
            staging = self.out / f'archive-{index}'
            staging.mkdir()
            entries = []
            for i, (key, (member, data)) in enumerate(sorted(after.items())):
                disk = staging / str(i)
                disk.write_bytes(data)
                entries.append(f'{disk}|{member}\n')
            listing = staging / 'members.list'
            listing.write_text(''.join(entries))
            dest = self.out / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            self.run('create', dest, listing)
            actual = self.members(dest)
            require(set(actual) - {'(listfile)'} == set(after), 'Output resource set differs')
            inventory = []
            for key, (member, data) in sorted(after.items()):
                require(actual[key][1] == data, f'Roundtrip mismatch: {member}')
                previous = resources.get(key)
                inventory.append(dict(member=member, before_sha256=sha(previous[1]) if previous else None,
                                      after_sha256=sha(data), unchanged=bool(previous and previous[1] == data)))
            outputs[relative] = dict(sha256=file_sha(dest), resources_before=len(resources),
                resources_after=len(after), map_change=map_info, inventory=inventory,
                unchanged_resources=sum(r['unchanged'] for r in inventory),
                listfile=dict(before_sha256=sha(before['(listfile)'][1]),
                              after_sha256=sha(actual['(listfile)'][1]), expected_regenerated=True))
        for archive, info in self.archives.items():
            require(file_sha(Path(archive)) == info['sha256'], f'Input changed during build: {archive}')
        report = dict(status='staged only', baseline=BASE_HASHES, outputs=outputs,
            loading_change=loading_info, art=art_info, snapshot_override_audit=audit,
            turtle_art_priority_audit=turtle_art_audit,
            sources=self.sources, archives=self.archives,
            priority_result=dict(scope='Known snapshot plus coordinated r5 archives only',
                map800_all_three_archives=511, loading511='Data/patch-T.MPQ',
                art_root_z_and_t_identical=art_info['normalized_sha256'], has_wide_screen=0),
            limitations=['Reference snapshot does not establish actual playing-client priority.',
                'No in-game loading-screen test performed.',
                'No source cleanup: older art remains in read-only source archives; output root Z replaces it.',
                'MPQ container/listfile metadata regenerated; all other resource content hashes verified.'])
        (self.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({p: v['sha256'] for p, v in outputs.items()}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'work/client-overlay-r5')
    args = parser.parse_args()
    LoadingBuilder(args.output.resolve(), Path('/home/dev/wow-335'),
                   Path('/home/dev/wow-turtle'), BASE).build()


if __name__ == '__main__':
    main()
