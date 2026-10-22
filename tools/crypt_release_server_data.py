"""Server-only binary payload validation and generic DBC delta application."""
import struct
from pathlib import Path

from crypt_release_client import require, sha, relative
from crypt_release_dbc import parse_dbc, merge_dbc, string_at

DELTAS = {
    'Map.dbc': (66, [800], [1, *range(5, 21), *range(23, 39), *range(40, 56)], False),
    'AreaTable.dbc': (36, [5086], list(range(11, 27)), False),
    'MapDifficulty.dbc': (23, [756], [*range(3, 19), 22], False),
    'WorldMapArea.dbc': (11, [674], [3], False),
    'AreaTrigger.dbc': (10, [900800, 900801], [], True),
}
CLOSURE_SHA = '9d6e22e79f34e36ab7735bd29f272faabe61f4099554756128e8d4de1d94c24f'


def tile_models(raw):
    require(raw[:8] == b'VMAP_4.8' and len(raw) >= 12, 'Invalid vmtile header')
    count, = struct.unpack_from('<I', raw, 8)
    require(count < 100000, 'Unreasonable spawn count')
    pos, names = 12, set()
    for _ in range(count):
        require(pos + 38 <= len(raw), 'Truncated ModelSpawn')
        flags, = struct.unpack_from('<I', raw, pos)
        require(flags & ~7 == 0, 'Unknown ModelSpawn flags')
        pos += 38 + (24 if flags & 4 else 0)
        require(pos + 4 <= len(raw), 'Truncated ModelSpawn name')
        size, = struct.unpack_from('<I', raw, pos)
        pos += 4
        require(0 < size <= 500 and pos + size + 4 <= len(raw), 'Invalid ModelSpawn name')
        # Exactly the loader's C-string resolution, including serialized trailing NUL.
        name = (raw[pos:pos + size] + b'.vmo').split(b'\0')[0].decode('ascii')
        require(len(relative(name).parts) == 1, 'Non-flat model name')
        names.add(name)
        pos += size + 4  # tree node index
    require(pos == len(raw), 'Trailing vmtile bytes')
    return names


def binary_check(name, raw):
    if name.endswith('.map'):
        require(raw[:12] == b'MAPS' + struct.pack('<II', 9, 12340), 'Incompatible terrain header')
    elif name.endswith(('.vmtree', '.vmtile')):
        require(raw[:8] == b'VMAP_4.8', 'Incompatible VMap header')
    elif name.endswith('.mmap'):
        require(len(raw) == 28, 'Incompatible mmap params')
    elif name.endswith('.mmtile'):
        require(len(raw) >= 64, 'Truncated mmap tile')
        magic, detour, version, size = struct.unpack_from('<4I', raw)
        require(magic == 0x4d4d4150 and detour == 7 and version == 20 and
                size == len(raw) - 56, 'Incompatible mmap header')
        require(struct.unpack_from('<II', raw, 56) == (0x444e4156, 7), 'Incompatible Detour header')


def server_payload(root):
    root = Path(root)
    result = {}
    patterns = [('maps', '800*.map', 6), ('vmaps', '800*.vmtree', 1),
                ('vmaps', '800*.vmtile', 6), ('mmaps', '800*.mmap', 1),
                ('mmaps', '800*.mmtile', 6)]
    names = set()
    for directory, pattern, count in patterns:
        paths = sorted((root / directory).glob(pattern))
        require(len(paths) == count, f'Expected {count} {directory}/{pattern}')
        for path in paths:
            require(not path.is_symlink(), 'Symlink server payload')
            raw = path.read_bytes()
            binary_check(path.name, raw)
            result[f'{directory}/{path.name}'] = raw
            if path.suffix == '.vmtile':
                names.update(tile_models(raw))
    lines = []
    for name in sorted(names):
        path = root / 'vmaps' / name
        require(path.is_file() and not path.is_symlink(), f'Missing model: {name}')
        raw = path.read_bytes()
        result['vmaps/' + name] = raw
        lines.append(f'vmaps/{name}\t{len(raw)}\t{sha(raw)}\n')
    require(len(names) == 405 and sum(len(result['vmaps/' + n]) for n in names) == 5691196
            and sha(''.join(lines).encode()) == CLOSURE_SHA, 'Pilot model closure fingerprint mismatch')
    require('Tw800Crypt.wmo.vmo' in names, 'Missing isolated crypt model')
    for name, (fields, ids, strings, order) in DELTAS.items():
        raw = (root / 'dbc' / name).read_bytes()
        n, rows, block = parse_dbc(raw)
        require(n == fields, f'Unexpected server DBC schema: {name}')
        selected = [r for r in rows if r[0] in ids]
        require(len(selected) == len(ids), f'Missing donor rows: {name}')
        if name == 'Map.dbc':
            require(selected[0][57] == 0, 'Server Map loading screen must remain zero')
        # Compact donor; merge_dbc reconstructs only the selected rows and strings.
        empty = struct.pack('<4s4I', b'WDBC', 0, fields, fields * 4, 1) + b'\0'
        result['dbc/' + name] = merge_dbc(empty, raw, ids, strings, order)
    return result


def merge_server(root, donors):
    root = Path(root)
    require(not any(p.is_dir() for p in (root / 'dbc').iterdir()),
            'Locale DBC subtrees require an explicit separate migration')
    result = {}
    for name, (fields, ids, strings, order) in DELTAS.items():
        raw = (root / 'dbc' / name).read_bytes()
        n, rows, block = parse_dbc(raw)
        require(n == fields, f'Unexpected target DBC schema: {name}')
        for row in rows:
            if name == 'Map.dbc':
                require(row[0] == 800 or string_at(block, row[1]).lower() != b'karazhancrypt',
                        'KarazhanCrypt directory collision')
            if name == 'AreaTable.dbc':
                require(row[0] == 5086 or row[1] != 800, 'Map800 area binding collision')
            if name in ('MapDifficulty.dbc', 'WorldMapArea.dbc', 'AreaTrigger.dbc'):
                require(row[0] in ids or row[1] != 800, f'Map800 secondary collision: {name}')
            if name == 'WorldMapArea.dbc':
                require(row[0] == 674 or row[2] != 5086, 'Area5086 world map binding collision')
        result['dbc/' + name] = merge_dbc(raw, donors['dbc/' + name], ids, strings, order)
    return result


def baseline_check(root):
    for directory, pattern in [('maps', '000*.map'), ('vmaps', '000*.vmtree'),
                               ('mmaps', '000*.mmtile'), ('mmaps', '000.mmap')]:
        samples = sorted((Path(root) / directory).glob(pattern))
        require(samples, f'Missing compatible baseline sample: {directory}/{pattern}')
        binary_check(samples[0].name, samples[0].read_bytes())
