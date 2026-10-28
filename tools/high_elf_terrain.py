#!/usr/bin/env python3
"""Cell-wise, lossless-terrain ADT/v18 composition; never writes a WDT or MPQ.

Layout references: https://wowdev.wiki/ADT/v18 (MCNK, MCRF, MH2O), and
src/tools/map_extractor/adt.h in AzerothCore. MCNK offsets include its eight
byte chunk header; MH2O offsets exclude it. MCNR padding and zero-sized legacy
MCLQ headers prohibit walking MCNK subchunks by their declared sizes.

Objects are owned by their anchor cell when referenced there, otherwise by the
nearest referencing cell (squared distance to its rectangle, slot tie-break).
An object belonging to replaced terrain is not resurrected by an overlapping
reference outside it. References only come from the chosen side of each cell.
Identity is type + UID + resolved name + all remaining placement bytes. UID
conflicts within a tile fail rather than inventing IDs; cross-tile byte
differences are reported in the candidate manifest. Unreferenced
native records are retained only if their anchor is in a native cell.
The single-tile API can only determine local owners. The region builder pools
references across its inputs before composing, so an object owned in a replaced
neighbor cannot return through the native side of another tile.

Liquid policy: same-side MH2O is authoritative in cells with one or more
layers. Verify active MCLQ framing and set its own payload size before clearing
legacy liquid flags (0x3c), ofsLiquid and sizeLiquid; retain the opaque payload.
Cells without MH2O layers retain legacy water.
Final builds additionally apply the pinned, explicit adaptations in the compact
selection manifest: two residual layers, area IDs and evidence-based UID fixes.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess

from adt import CHUNK_MAGIC, MHDR_FIELDS, _adt_layout
from adt_refs import name_offsets
from adt_client import scan_mcnk, self_length_mclq

ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT / 'tools/high-elf-terrain-selection.json'
AREA_MAP = ROOT / 'tools/high-elf-map.json'
POINTERS = ((0x1C, b'TVCM'), (0x20, b'RNCM'), (0x24, b'YLCM'),
            (0x28, b'FRCM'), (0x2C, b'LACM'), (0x34, b'HSCM'),
            (0x60, b'ESCM'), (0x68, b'QLCM'), (0x7C, b'VCCM'))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def u32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def chunk(magic, body):
    return magic + struct.pack('<I', len(body)) + body


def uints(body):
    if len(body) % 4:
        raise ValueError('unaligned uint32 table')
    return [v[0] for v in struct.iter_unpack('<I', body)]


class Tile:
    """Strict referenced structures; opaque terrain payloads stay opaque."""
    def __init__(self, data):
        self.data = data
        _, self.header, self.offsets, self.entries, self.ends = _adt_layout(data)
        self.cells = [data[p:self.ends[p]] if p else None
                      for p, _, _, _ in self.entries]
        self.coords = {}
        for i, cell in enumerate(self.cells):
            if cell is not None:
                xy = struct.unpack_from('<2I', cell, 12)
                if xy != (i % 16, i // 16):
                    raise ValueError('MCIN slot does not match MCNK coordinates')
                self.coords[i] = xy
        self.textures = list(name_offsets(self.body('mtex')).values())
        self.refs = [self.cell_refs(c) if c else ([], []) for c in self.cells]
        self.placements = []
        for names_key, ids_key, placements_key, size in (
                ('mmdx', 'mmid', 'mddf', 36), ('mwmo', 'mwid', 'modf', 64)):
            names = name_offsets(self.body(names_key))
            ids = uints(self.body(ids_key))
            if any(i not in names for i in ids):
                raise ValueError('name index is not a string start')
            body = self.body(placements_key)
            if len(body) % size:
                raise ValueError('misaligned placement table')
            records = []
            for p in range(0, len(body), size):
                raw = body[p:p + size]
                index = u32(raw, 0)
                if index >= len(ids):
                    raise ValueError('placement name index out of bounds')
                records.append((names[ids[index]], raw))
            self.placements.append(records)
        for refs in self.refs:
            for kind in range(2):
                if any(r >= len(self.placements[kind]) for r in refs[kind]):
                    raise ValueError('MCRF placement index out of bounds')

    def body(self, key):
        p = self.offsets[key]
        return self.data[p + 8:self.ends[p]] if p else b''

    @staticmethod
    def sub(cell, field, magic):
        p = u32(cell, field)
        if p < 136 or p + 8 > len(cell) or cell[p:p + 4] != magic:
            raise ValueError('invalid %r MCNK offset' % magic)
        end = p + 8 + u32(cell, p + 4)
        if end > len(cell):
            raise ValueError('MCNK subchunk exceeds cell')
        return p, end

    @classmethod
    def cell_refs(cls, cell):
        nd, nw = u32(cell, 0x18), u32(cell, 0x40)
        if not u32(cell, 0x28) and not (nd + nw):
            return [], []
        p, end = cls.sub(cell, 0x28, b'FRCM')
        if end - p - 8 != (nd + nw) * 4:
            raise ValueError('MCRF size does not match both reference counts')
        values = uints(cell[p + 8:end])
        return values[:nd], values[nd:]

    def anchor(self, raw):
        if not self.coords:
            raise ValueError('cannot locate placement in empty tile')
        i = next(iter(self.coords))
        cell = self.cells[i]
        north, west = struct.unpack_from('<2f', cell, 0x70)
        x, _, z = struct.unpack_from('<3f', raw, 8)
        # Placement coordinates grow east/south from the map's NW corner.
        origin = 1600.0 / 3 * 32
        cx, cy = self.coords[i]
        return ((x - (origin - west)) / (100.0 / 3) + cx,
                (z - (origin - north)) / (100.0 / 3) + cy)

    def owners(self, kind):
        memberships = [set() for _ in self.placements[kind]]
        for slot, refs in enumerate(self.refs):
            for r in refs[kind]:
                memberships[r].add(slot)
        result = []
        for (_, raw), refs in zip(self.placements[kind], memberships):
            x, y = self.anchor(raw)
            if not (math.isfinite(x) and math.isfinite(y)):
                raise ValueError('nonfinite placement anchor')
            anchor = math.floor(y) * 16 + math.floor(x)
            if not refs:
                result.append(anchor if 0 <= x < 16 and 0 <= y < 16 else None)
                continue
            if 0 <= x < 16 and 0 <= y < 16 and anchor in refs:
                result.append(anchor)
                continue
            def distance(slot):
                cx, cy = self.coords[slot]
                return (max(cx - x, 0, x - cx - 1) ** 2 +
                        max(cy - y, 0, y - cy - 1) ** 2, slot)
            result.append(min(refs, key=distance))
        return result


def liquid_cells(body):
    """Resolve all WotLK LVF 0/1/2 layers, with optional data offsets."""
    if not body:
        return [(b'', []) for _ in range(256)]
    if len(body) < 3072:
        raise ValueError('truncated MH2O directory')

    def take(p, n):
        if p < 3072 or p + n > len(body):
            raise ValueError('MH2O nested offset out of bounds')
        return body[p:p + n]

    cells = []
    for i in range(256):
        p, count, attr = struct.unpack_from('<3I', body, i * 12)
        attributes = take(attr, 16) if attr else b''
        layers = []
        records = take(p, count * 24) if count else b''
        for j in range(count):
            record = records[j * 24:(j + 1) * 24]
            lvf = struct.unpack_from('<H', record, 2)[0]
            x, y, w, h = record[12:16]
            if lvf not in (0, 1, 2) or not (1 <= w <= 8 and 1 <= h <= 8
                                                       and x + w <= 8 and y + h <= 8):
                raise ValueError('unsupported WotLK MH2O vertex format/rectangle')
            bitmap, vertex = struct.unpack_from('<2I', record, 16)
            mask = take(bitmap, (w * h + 7) // 8) if bitmap else b''
            vertices = take(vertex, (w + 1) * (h + 1) * (5, 8, 1)[lvf]) if vertex else b''
            layers.append((record[:16], mask, vertices))
        cells.append((attributes, layers))
    return cells


def compose_liquid(native, source, selected):
    sides = [liquid_cells(t.body('mh2o')) for t in (native, source)]
    if not any(t.offsets['mh2o'] for t in (native, source)):
        return None
    out = bytearray(3072)

    def emit(data):
        if not data:
            return 0
        p = len(out)
        out.extend(data)
        return p

    for i in range(256):
        attributes, layers = sides[i in selected][i]
        p = emit(bytes(24 * len(layers)))
        attr = emit(attributes)
        struct.pack_into('<3I', out, i * 12, p, len(layers), attr)
        for j, (record, mask, vertices) in enumerate(layers):
            mask_p, vertices_p = emit(mask), emit(vertices)
            out[p + j * 24:p + j * 24 + 16] = record
            struct.pack_into('<2I', out, p + j * 24 + 16, mask_p, vertices_p)
    return bytes(out)


def _name_key(name):
    return name.replace(b'/', b'\\').lower()


def _objects(tiles, selected, kind, mapper, ownership=None):
    names, ids, records, identities, uids = [], {}, [], {}, {}
    keys = []
    for side, tile in enumerate(tiles):
        side_keys = []
        for (name, raw), owner in zip(tile.placements[kind], tile.owners(kind)):
            if side and mapper:
                replacement = mapper(name.decode('latin1'))
                if replacement is not None:
                    name = replacement.encode('latin1')
            if not name or b'\0' in name:
                raise ValueError('invalid mapped object name')
            identity = (_name_key(name), raw[4:])
            side_keys.append(identity)
            owned_by_source = (ownership.get((side, kind, identity))
                               if ownership is not None else
                               (owner in selected if owner is not None else None))
            if owned_by_source is None or owned_by_source != bool(side):
                continue
            if identity in identities:
                continue
            uid = u32(raw, 4)
            if uid in uids and uids[uid] != identity:
                raise ValueError('conflicting retained placement UID %d' % uid)
            uids[uid] = identity
            nk = _name_key(name)
            if nk not in ids:
                ids[nk] = len(names)
                names.append(name)
            identities[identity] = len(records)
            records.append(struct.pack('<I', ids[nk]) + raw[4:])
        keys.append(side_keys)
    # A shared identity can supply references on either side of the boundary.
    maps = [{i: identities[key] for i, key in enumerate(ks) if key in identities}
            for ks in keys]
    name_body, offsets = bytearray(), bytearray()
    for name in names:
        offsets.extend(struct.pack('<I', len(name_body)))
        name_body.extend(name + b'\0')
    return bytes(name_body), bytes(offsets), b''.join(records), maps


def _patch_cell(cell, texture_map, refs, area_map):
    out = bytearray(cell)
    layers = u32(out, 0x14)
    if layers or u32(out, 0x24):
        p, end = Tile.sub(out, 0x24, b'YLCM')
        if end - p - 8 != layers * 16:
            raise ValueError('MCLY layer count mismatch')
        for j in range(layers):
            q = p + 8 + j * 16
            old = u32(out, q)
            if old >= len(texture_map):
                raise ValueError('MCLY material index out of bounds')
            struct.pack_into('<I', out, q, texture_map[old])
    area = u32(out, 0x3C)
    struct.pack_into('<I', out, 0x3C, area_map.get(area, area))
    body = struct.pack('<%dI' % (len(refs[0]) + len(refs[1])), *(refs[0] + refs[1]))
    replacement = chunk(b'FRCM', body)
    if u32(out, 0x28):
        p, end = Tile.sub(out, 0x28, b'FRCM')
    else:
        p = end = len(out)
    delta = len(replacement) - (end - p)
    # Only genuine subchunk pointers are relocated; dry MCLQ sentinels and
    # Vanilla's unused textureId (later ofsMCCV) must remain byte-exact.
    for field, magic in ((0x1C, b'TVCM'), (0x20, b'RNCM'), (0x24, b'YLCM'),
                         (0x2C, b'LACM'), (0x34, b'HSCM'), (0x60, b'ESCM'),
                         (0x68, b'QLCM'), (0x7C, b'VCCM')):
        old = u32(out, field)
        if end <= old < len(out) and out[old:old + 4] == magic:
            struct.pack_into('<I', out, field, old + delta)
    struct.pack_into('<I', out, 0x28, p)
    struct.pack_into('<I', out, 0x18, len(refs[0]))
    struct.pack_into('<I', out, 0x40, len(refs[1]))
    out[p:end] = replacement
    struct.pack_into('<I', out, 4, len(out) - 8)
    return bytes(out)


def replace_subchunk(cell, field, magic, body):
    """Splice one referenced block without walking MCNR/MCLQ framing."""
    p, end = Tile.sub(cell, field, magic)
    replacement = chunk(magic, body)
    delta = len(replacement) - (end - p)
    out = bytearray(cell)
    for other, expected in POINTERS:
        old = u32(out, other)
        if end <= old < len(out) and out[old:old + 4] == expected:
            struct.pack_into('<I', out, other, old + delta)
    out[p:end] = replacement
    struct.pack_into('<I', out, 4, len(out) - 8)
    return bytes(out)


def remove_residual_layer(cell, textures, rule):
    """Only the named, hash-pinned 2048-byte packed-alpha layer is removable.

    Keep all surviving alpha bytes and flags. Remap the 2-bit predominant
    texture indices as well; refuse a removed dominant layer rather than guess
    a replacement ground effect. Neither approved residual is predominant.
    """
    lp, le = Tile.sub(cell, 0x24, b'YLCM')
    ap, ae = Tile.sub(cell, 0x2C, b'LACM')
    layers = [list(struct.unpack_from('<4I', cell, p)) for p in range(lp + 8, le, 16)]
    drop = rule['layer']
    if not 0 < drop < len(layers) or textures[layers[drop][0]] != rule['texture'].encode():
        raise ValueError('residual layer identity changed')
    masks = []
    for j, layer in enumerate(layers[1:], 1):
        end = layers[j + 1][2] if j + 1 < len(layers) else ae - ap - 8
        mask = cell[ap + 8 + layer[2]:ap + 8 + end]
        if len(mask) != 2048 or layer[1] & 0x300 != 0x100:
            raise ValueError('residual adaptation requires packed 4-bit alpha')
        masks.append(mask)
    removed = masks[drop - 1]
    if digest(removed) != rule['alpha_sha256']:
        raise ValueError('residual alpha hash changed')
    decoded = [[v / 15 for b in mask for v in (b & 15, b >> 4)] for mask in masks]
    effective = [a * math.prod(1 - upper[i] for upper in decoded[drop:])
                 for i, a in enumerate(decoded[drop - 1])]
    measured = sum(effective) / 4096 * 100
    if sum(v != 0 for v in effective) != rule['effective_nonzero_samples'] or abs(
            measured - rule['effective_percent']) > 1e-10:
        raise ValueError('residual effective contribution changed')
    out = bytearray(cell)
    for p in range(0x48, 0x58):
        remapped = 0
        for shift in (0, 2, 4, 6):
            old = (out[p] >> shift) & 3
            if old == drop:
                raise ValueError('residual layer became predominant')
            remapped |= (old - (old > drop)) << shift
        out[p] = remapped
    alpha, surviving = bytearray(), [layers[0]]
    for j, mask in enumerate(masks, 1):
        if j != drop:
            layer = layers[j]
            layer[2] = len(alpha)
            alpha.extend(mask)
            surviving.append(layer)
    # Both native/source v18 sizeAlpha conventions accepted by the parser.
    size_includes_header = u32(cell, 0x30) == ae - ap
    if not size_includes_header and u32(cell, 0x30) != ae - ap - 8:
        raise ValueError('unexpected sizeAlpha convention')
    struct.pack_into('<I', out, 0x14, len(surviving))
    struct.pack_into('<I', out, 0x30, len(alpha) + (8 if size_includes_header else 0))
    out = replace_subchunk(bytes(out), 0x2C, b'LACM', alpha)
    return replace_subchunk(out, 0x24, b'YLCM', b''.join(struct.pack('<4I', *r) for r in surviving))


def compose_adt(native: bytes, source: bytes, selected_indices: set[int],
                area_map: dict = {}, model_map=None, wmo_map=None) -> bytes:
    """Compose MCIN slots 0..255. Maps apply only to source-selected content.

    area_map maps IDs; model_map/wmo_map receive latin1 str and return str or
    None (keep). The default dictionary is never mutated. All placements retain
    their UID and every byte after nameId. No positional deduplication is used.
    """
    return _compose_adt(native, source, selected_indices, area_map, model_map, wmo_map)


def _compose_adt(native, source, selected_indices, area_map, model_map, wmo_map,
                 ownership=None, residuals=None):
    selected = set(selected_indices)
    if any(type(i) is not int or not 0 <= i < 256 for i in selected):
        raise ValueError('selected_indices must contain MCIN indices 0..255')
    tiles = [Tile(native), Tile(source)]
    textures, texture_ids, texture_maps, texture_flags = [], {}, [], []
    for tile in tiles:
        flags = uints(tile.body('mtxf'))
        if flags and len(flags) != len(tile.textures):
            raise ValueError('MTXF does not match MTEX')
        mapping = []
        for j, name in enumerate(tile.textures):
            flag = flags[j] if flags else 0
            # MTXF participates in identity: same path with different flags
            # needs two MTEX slots to preserve material semantics.
            key = (_name_key(name), flag)
            if key not in texture_ids:
                texture_ids[key] = len(textures)
                textures.append(name)
                texture_flags.append(flag)
            mapping.append(texture_ids[key])
        texture_maps.append(mapping)
    bodies = {'mtex': b''.join(n + b'\0' for n in textures)}
    ref_maps = []
    for kind, mapper, names, ids, placements in (
            (0, model_map, 'mmdx', 'mmid', 'mddf'),
            (1, wmo_map, 'mwmo', 'mwid', 'modf')):
        bodies[names], bodies[ids], bodies[placements], maps = _objects(
            tiles, selected, kind, mapper, ownership)
        ref_maps.append(maps)
    bodies['mh2o'] = compose_liquid(*tiles, selected)
    liquids = liquid_cells(bodies['mh2o'] or b'')
    bodies['mtxf'] = (struct.pack('<%dI' % len(texture_flags), *texture_flags)
                      if any(t.offsets['mtxf'] for t in tiles) else None)
    cells, entries = {}, []
    for i in range(256):
        side = int(i in selected)
        tile = tiles[side]
        entries.append(tile.entries[i])
        cell = tile.cells[i]
        if cell is None:
            if side:
                raise ValueError('selected source cell missing')
            continue
        refs = [[ref_maps[k][side][r] for r in tile.refs[i][k]
                 if r in ref_maps[k][side]] for k in range(2)]
        cells[i] = _patch_cell(cell, texture_maps[side], refs,
                               area_map if side else {})
        if residuals and i in residuals:
            if not side:
                raise ValueError('residual adaptation must target source terrain')
            cells[i] = remove_residual_layer(cells[i], textures, residuals[i])
        if liquids[i][1]:
            adapted = bytearray(self_length_mclq(cells[i]))
            struct.pack_into('<I', adapted, 8, u32(adapted, 8) & ~0x3C)
            struct.pack_into('<2I', adapted, 0x68, 0, 0)
            cells[i] = bytes(adapted)
        scan_mcnk(cells[i])
    # Remove unused MTEX/MTXF entries, including the two missing error textures.
    # No aliases: every surviving MCLY still resolves to its original material.
    used = set()
    for cell in cells.values():
        if u32(cell, 0x14):
            p, end = Tile.sub(cell, 0x24, b'YLCM')
            used.update(u32(cell, j) for j in range(p + 8, end, 16))
    ordered = sorted(used)
    compact = {old: new for new, old in enumerate(ordered)}
    for i, cell in cells.items():
        out = bytearray(cell)
        if u32(cell, 0x14):
            p, end = Tile.sub(cell, 0x24, b'YLCM')
            for j in range(p + 8, end, 16):
                struct.pack_into('<I', out, j, compact[u32(out, j)])
        cells[i] = bytes(out)
    bodies['mtex'] = b''.join(textures[j] + b'\0' for j in ordered)
    if bodies['mtxf'] is not None:
        bodies['mtxf'] = struct.pack('<%dI' % len(ordered), *(texture_flags[j] for j in ordered))
    # Native tile-wide opaque chunks (including MFBO) and MHDR reserved fields
    # are retained. WDT is deliberately outside this API.
    n = tiles[0]
    out = bytearray(native[:12] + chunk(b'RDHM', bytes(64)) + chunk(b'NICM', bytes(4096)))
    positions = {'mcin': 84}
    emitted = set()
    keys = {p: k for k, p in n.offsets.items() if p}
    for p, end in n.ends.items():
        if p in (0, 12, n.offsets['mcin']) or native[p:p + 4] == b'KNCM':
            continue
        key = keys.get(p)
        if key in bodies:
            body = bodies[key]
            emitted.add(key)
            if body is None:
                continue
            raw = chunk(CHUNK_MAGIC[key], body)
        else:
            raw = native[p:end]
        if key:
            positions[key] = len(out)
        out.extend(raw)
    for key, body in bodies.items():
        if key not in emitted and body is not None:
            positions[key] = len(out)
            out.extend(chunk(CHUNK_MAGIC[key], body))
    for i, cell in cells.items():
        struct.pack_into('<4I', out, 92 + i * 16, len(out), len(cell), *entries[i][2:])
        out.extend(cell)
    for i in range(256):
        if i not in cells:
            struct.pack_into('<4I', out, 92 + i * 16, 0, 0, *entries[i][2:])
    header = list(n.header)
    for j, key in enumerate(MHDR_FIELDS[1:12], 1):
        header[j] = positions[key] - 20 if key in positions else 0
    struct.pack_into('<16I', out, 20, *header)
    result = bytes(out)
    validated = Tile(result)  # framing, names and both MCRF index spaces
    liquid_cells(validated.body('mh2o'))
    # AzerothCore VMap uses one instance UID namespace for M2 and WMO.
    model_uids = {u32(raw, 4) for _, raw in validated.placements[0]}
    if any(u32(raw, 4) in model_uids for _, raw in validated.placements[1]):
        raise ValueError('conflicting retained UID between MDDF and MODF')
    return result


def compose_region(inputs, selection, area_map=None, model_map=None, wmo_map=None,
                   residuals=()):
    """Compose a tile batch with shared reference ownership, no file writes.

    inputs: {tile_xy: (native_bytes, source_bytes)}, including audited neighbors.
    selection: {output_tile_xy: selected_source_slots}. Other tiles are native.
    Ownership uses the same nearest-reference rule in global cell coordinates.
    Repeated placements across tiles keep one identity and their original UID.
    """
    memberships, anchors = {}, {}
    for xy, pair in inputs.items():
        for side, data in enumerate(pair):
            tile = Tile(data)
            for kind, mapper in enumerate((model_map, wmo_map)):
                keys = []
                for name, raw in tile.placements[kind]:
                    if side and mapper:
                        replacement = mapper(name.decode('latin1'))
                        if replacement is not None:
                            name = replacement.encode('latin1')
                    key = side, kind, (_name_key(name), raw[4:])
                    keys.append(key)
                    memberships.setdefault(key, set())
                    x, _, z = struct.unpack_from('<3f', raw, 8)
                    anchors[key] = x / (100 / 3), z / (100 / 3)
                for slot, refs in enumerate(tile.refs):
                    cell = xy[0] * 16 + slot % 16, xy[1] * 16 + slot // 16
                    for r in refs[kind]:
                        memberships[keys[r]].add(cell)
    ownership = {}
    for key, refs in memberships.items():
        x, y = anchors[key]
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError('nonfinite placement anchor')
        anchor = math.floor(x), math.floor(y)
        if anchor in refs or not refs:
            owner = anchor
        else:
            def distance(cell):
                cx, cy = cell
                return (max(cx - x, 0, x - cx - 1) ** 2 +
                        max(cy - y, 0, y - cy - 1) ** 2, cy, cx)
            owner = min(refs, key=distance)
        xy = owner[0] // 16, owner[1] // 16
        slot = owner[1] % 16 * 16 + owner[0] % 16
        ownership[key] = slot in selection.get(xy, set())
    outputs = {xy: _compose_adt(*inputs[xy], selected, area_map or {}, model_map,
                               wmo_map, ownership,
                               {r['slot']: r for r in residuals if tuple(r['tile']) == xy})
               for xy, selected in sorted(selection.items())}
    return outputs


def region_uid_conflicts(tiles):
    """Report cross-tile byte differences without changing original placements."""
    seen, conflicts = {}, []
    for xy, tile in sorted(tiles.items()):
        for kind, records in enumerate(tile.placements):
            for name, raw in records:
                key, identity = u32(raw, 4), (kind, _name_key(name), raw[4:])
                previous = seen.get(key)
                if previous is not None and previous[1] != identity:
                    conflicts.append(dict(kind=('mddf', 'modf')[kind], uid=key,
                                          first_tile=previous[0], tile=xy,
                                          first_kind=('mddf', 'modf')[previous[1][0]],
                                          first_name=previous[1][1].decode('latin1'),
                                          name=name.decode('latin1'),
                                          first_payload_hex=previous[1][2].hex(),
                                          payload_hex=raw[4:].hex()))
                else:
                    seen[key] = xy, identity
    return conflicts


def load_plan(path=SELECTION):
    """The checked-in compact selection is the only selection dependency."""
    plan = json.loads(Path(path).read_text())
    selection = {}
    for key, encoded in plan['selection'].items():
        tile = tuple(map(int, key.split('_')))
        bits = bytes.fromhex(encoded)
        if len(tile) != 2 or len(bits) != 32:
            raise ValueError('invalid compact terrain selection')
        mask = int.from_bytes(bits, 'little')
        selection[tile] = {i for i in range(256) if mask & (1 << i)}
    if len(selection) != 24 or sum(map(len, selection.values())) != 3899:
        raise ValueError('compact selection count changed')
    return plan, selection


def load_inputs(root, plan):
    result = {}
    for key, expected in plan['inputs'].items():
        xy = tuple(map(int, key.split('_')))
        pair = tuple(tile_path(root, side, xy).read_bytes() for side in ('335', 'turtle'))
        if list(map(digest, pair)) != expected:
            raise ValueError('terrain input hash mismatch: ' + key)
        result[xy] = pair
    return result


def source_model(name):
    return name[:-4] + '.m2' if name.lower().endswith('.mdx') else name


READER_CPP = r'''
#include <StormLib.h>
#include <cstdio>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>
int main(int argc, char** argv) {
    std::vector<HANDLE> arcs;
    for (int i=1;i<argc;++i) {
        HANDLE h=nullptr;
        if (!SFileOpenArchive(argv[i],0,MPQ_OPEN_READ_ONLY,&h)) return 2;
        arcs.push_back(h);
    }
    std::string name;
    while (std::getline(std::cin,name)) {
        uint32_t header[3]={0,0,0}; std::vector<char> bytes;
        for (uint32_t i=0;i<arcs.size();++i) {
            HANDLE f=nullptr;
            if (!SFileOpenFileEx(arcs[i],name.c_str(),SFILE_OPEN_FROM_MPQ,&f)) {
                if (SErrGetLastError()!=ERROR_FILE_NOT_FOUND) {
                    header[0]=2;header[1]=i;header[2]=SErrGetLastError();break;
                }
                continue;
            }
            DWORD high=0,n=SFileGetFileSize(f,&high),got=0;
            if (high || n==0xffffffff || n>64*1024*1024) {SFileCloseFile(f);return 3;}
            if (!n) {SFileCloseFile(f);header[0]=3;header[1]=i;break;}
            bytes.resize(n);
            bool ok=n && SFileReadFile(f,bytes.data(),n,&got,nullptr) && got==n;
            SFileCloseFile(f); header[0]=ok?1:2;header[1]=i;header[2]=ok?n:0;break;
        }
        if (fwrite(header,sizeof(header),1,stdout)!=1) return 4;
        if (header[0]==1 && fwrite(bytes.data(),1,bytes.size(),stdout)!=bytes.size()) return 4;
        fflush(stdout);
    }
    for (auto h:arcs) SFileCloseArchive(h);
}
'''


def archive_order(root, side):
    """Explicit offline snapshot order, esES locale overrides root patches.

    Probe all 4096 map0 names directly; do not depend on MPQ listfile coverage.
    These are read-only source clients, not the user's playing-client order.
    """
    data = root / 'Data'
    base = (['wmo', 'texture', 'terrain', 'speech', 'sound', 'model', 'misc',
             'interface', 'fonts', 'dbc', 'base', 'backup'] if side == 'turtle' else
            ['common', 'common-2', 'expansion', 'lichking', 'backup-eses',
             'base-eses', 'speech-eses', 'locale-eses', 'expansion-locale-eses',
             'expansion-speech-eses', 'lichking-locale-eses', 'lichking-speech-eses'])

    def priority(p):
        stem = p.stem.lower()
        if stem in base:
            return 0, base.index(stem), 0
        match = re.fullmatch(r'patch(?:-eses)?(?:-([0-9a-z]+))?', stem)
        if not match:
            raise ValueError('unclassified archive ' + str(p))
        suffix = match[1] or '0'
        return 1, int(suffix) if suffix.isdigit() else 1000 + ord(suffix[0]), int(p.parent != data)

    arcs = [p for p in data.rglob('*') if p.suffix.lower() == '.mpq'
            and (p.parent == data or p.parent.name.lower() == 'eses')]
    if not arcs:
        raise ValueError('no snapshot archives: ' + str(root))
    return sorted(arcs, key=lambda p: (priority(p), str(p)), reverse=True)


def audit_map0(native_root, source_root, evidence, pinned_inputs, watched_uids, output_tiles):
    """Exhaustive UID occupancy audit of both effective map0 snapshots.

    Returns occupied UIDs separately from the JSON evidence, so no large cached
    work JSON is required to rebuild. Every ADT payload is hashed; UID scanning
    includes unreferenced MDDF/MODF records and one shared M2/WMO namespace.
    """
    evidence.mkdir(parents=True, exist_ok=True)
    cpp, binary = evidence / 'mpq-reader.cpp', evidence / 'mpq-reader'
    cpp.write_text(READER_CPP)
    subprocess.run(['g++', '-O2', '-std=c++17', '-I', str(ROOT / 'tools/stormlib/include'),
                    str(cpp), str(ROOT / 'tools/stormlib/lib/libstorm.a'),
                    '-lz', '-lbz2', '-lpthread', '-ldl', '-o', str(binary)], check=True)
    used, inventory, occurrences, external = set(), [], [], []
    counts, archive_lists, versions = {}, {}, {}
    for side, root in (('335', native_root), ('turtle', source_root)):
        archives = archive_order(root, side)
        archive_lists[side] = [str(p.relative_to(root)) for p in archives]
        process = subprocess.Popen([str(binary), *map(str, archives)],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        counts[side] = 0
        try:
            for x in range(64):
                for y in range(64):
                    xy = x, y
                    member = 'World\\Maps\\Azeroth\\Azeroth_%d_%d.adt' % xy
                    process.stdin.write(member.encode() + b'\n')
                    process.stdin.flush()
                    header = process.stdout.read(12)
                    if len(header) != 12:
                        raise ValueError('map0 reader stopped')
                    status, archive, size = struct.unpack('<3I', header)
                    if status == 2:
                        raise ValueError('map0 MPQ resource unreadable/deleted: %s (%s, code%d)' %
                                         (member, archives[archive], size))
                    if status == 3:
                        if xy in pinned_inputs:
                            raise ValueError('pinned terrain is an empty MPQ member')
                        inventory.append([side, x, y, archive_lists[side][archive], 'EMPTY'])
                        continue  # effective zero-size placeholder: no fallback
                    if status != 1:
                        if status:
                            raise ValueError('invalid MPQ reader status')
                        if xy in pinned_inputs:
                            raise ValueError('pinned terrain absent from snapshot')
                        continue
                    raw = process.stdout.read(size)
                    if len(raw) != size:
                        raise ValueError('short map0 ADT read')
                    sha = digest(raw)
                    if xy in pinned_inputs and sha != digest(pinned_inputs[xy][side == 'turtle']):
                        raise ValueError('effective snapshot differs from pinned terrain: ' + member)
                    inventory.append([side, x, y, archive_lists[side][archive], sha])
                    counts[side] += 1
                    # Only top-level name/placement tables are needed for UID
                    # occupancy; unrelated Vanilla MCNK water is not converted.
                    if (raw[:8] != b'REVM\x04\0\0\0' or u32(raw, 8) not in (18, 19)
                            or raw[12:16] != b'RDHM' or u32(raw, 16) != 64):
                        raise ValueError('unsupported map0 ADT version: %s %s %s' %
                                         (side, member, raw[:24].hex()))
                    version = side + ':' + str(u32(raw, 8))
                    versions[version] = versions.get(version, 0) + 1
                    def body(field, magic):
                        off = u32(raw, 20 + field * 4)
                        if not off:
                            return b''
                        p = 20 + off
                        if p + 8 > len(raw) or raw[p:p + 4] != magic:
                            raise ValueError('map0 audit placement chunk offset invalid')
                        end = p + 8 + u32(raw, p + 4)
                        if end > len(raw):
                            raise ValueError('truncated map0 placement chunk')
                        return raw[p + 8:end]
                    for kind, nf, ix, pf, stride in ((0, 3, 4, 7, 36), (1, 5, 6, 8, 64)):
                        records = body(pf, (b'FDDM', b'FDOM')[kind])
                        if len(records) % stride:
                            raise ValueError('misaligned map0 placements')
                        names = name_offsets(body(nf, (b'XDMM', b'OMWM')[kind]))
                        ids = uints(body(ix, (b'DIMM', b'DIWM')[kind]))
                        for p in range(0, len(records), stride):
                            record = records[p:p + stride]
                            uid = u32(record, 4)
                            used.add(uid)
                            if uid in watched_uids:
                                index = u32(record, 0)
                                if index >= len(ids) or ids[index] not in names:
                                    raise ValueError('invalid map0 placement name')
                                name = names[ids[index]].decode('latin1')
                                name = source_model(name) if side == 'turtle' and kind == 0 else name
                                item = dict(side=side, tile=xy, kind=kind, uid=uid, name=name,
                                            payload_hex=record[4:].hex())
                                if uid in (164208, 158149):
                                    occurrences.append(item)
                                if side == '335' and xy not in output_tiles:
                                    external.append(item)
        finally:
            process.stdin.close()
            process.stdout.close()
            if process.wait() != 0:
                raise ValueError('map0 reader failed')
    allocated = max(used, default=0) + 1
    if allocated > 0xFFFFFFFF:
        raise ValueError('UID namespace exhausted')
    audit = dict(schema=1, probed_names_per_snapshot=4096, present_adts=counts,
                 audited_top_level_versions=versions,
                 archive_priority=archive_lists, inventory=inventory,
                 content_sha256=digest(json.dumps(inventory, separators=(',', ':')).encode()),
                 occupied_uid_count=len(used), occupied_uid_max=max(used),
                 occupied_uid_sha256=digest(struct.pack('<%dI' % len(used), *sorted(used))),
                 allocated_uid=allocated, conflict_occurrences=occurrences)
    return audit, used, external


def resolve_uids(outputs, rules, allocated_uid, occupied):
    """Use existing conservative36_25 WMO bounds; allocate only the distinct tree."""
    if allocated_uid in occupied or not 0 < allocated_uid <= 0xFFFFFFFF:
        raise ValueError('replacement UID is not free in audited map0')
    canonical = bytes.fromhex(rules['canonical_payload_hex'])
    variant = bytes.fromhex(rules['variant_payload_hex'])
    tree = bytes.fromhex(rules['source_payload_hex'])
    if (len(canonical) != 60 or len(variant) != 60 or canonical[:28] != variant[:28]
            or canonical[52:] != variant[52:]):
        raise ValueError('WMO differs beyond bounds; cannot canonicalize')
    ca, va = struct.unpack_from('<6f', canonical, 28), struct.unpack_from('<6f', variant, 28)
    if not all(ca[j] <= va[j] and ca[j + 3] >= va[j + 3] for j in range(3)):
        raise ValueError('canonical WMO bounds do not contain source bounds')
    changed, results = [], {}
    for xy, data in sorted(outputs.items()):
        tile, out = Tile(data), bytearray(data)
        for kind, field in ((0, 'mddf'), (1, 'modf')):
            stride = (36, 64)[kind]
            for index, (name, raw) in enumerate(tile.placements[kind]):
                replacement = None
                if kind == 1 and u32(raw, 4) == rules['wmo_uid']:
                    if raw[4:] not in (canonical, variant):
                        raise ValueError('unknown WMO UID variant')
                    if raw[4:] == variant:
                        replacement = canonical
                if kind == 0 and raw[4:] == tree:
                    if not _name_key(name).endswith(b'\\plaguelandtree05.m2'):
                        raise ValueError('distinct source UID name changed')
                    replacement = struct.pack('<I', allocated_uid) + raw[8:]
                if replacement is not None:
                    p = tile.offsets[field] + 8 + index * stride + 4
                    out[p:p + stride - 4] = replacement
                    changed.append(dict(tile=xy, kind=field, old_uid=u32(raw, 4),
                                        new_uid=u32(replacement, 0), name=name.decode('latin1'),
                                        before_hex=raw[4:].hex(), after_hex=replacement.hex()))
        results[xy] = bytes(out)
    conflicts = region_uid_conflicts({xy: Tile(data) for xy, data in results.items()})
    if conflicts:
        raise ValueError('unresolved final region UID conflicts: ' + str(conflicts))
    return results, changed


def resolve_external_uids(outputs, external, inputs, occupied, allocated_uid):
    """Rename only source identities conflicting with untouched native map0.

    No retained native identity may be changed here. Full-map audit exposed
    reuse invisible to a24-tile-only check. Allocate in sorted identity order
    above BOTH snapshots' max UID, reserving the explicit tree allocation too.
    """
    native = {(kind, _name_key(name), raw[4:]) for xy in outputs
              for kind, records in enumerate(Tile(inputs[xy][0]).placements) for name, raw in records}
    external_ids = {}
    for item in external:
        identity = item['kind'], _name_key(item['name'].encode('latin1')), bytes.fromhex(item['payload_hex'])
        external_ids.setdefault(item['uid'], set()).add(identity)
    remap = {}
    for data in outputs.values():
        for kind, records in enumerate(Tile(data).placements):
            for name, raw in records:
                identity = kind, _name_key(name), raw[4:]
                uid = u32(raw, 4)
                if any(other != identity for other in external_ids.get(uid, ())):
                    if identity in native:
                        raise ValueError('unexpected native/native UID inconsistency')
                    remap[identity] = None
    ordered = sorted(remap, key=lambda identity: (u32(identity[2], 0), identity))
    evidence_hash = digest(json.dumps([[k, n.decode('latin1'), r.hex()] for k, n, r in ordered],
                                      separators=(',', ':')).encode())
    for i, identity in enumerate(ordered, 1):
        uid = allocated_uid + i
        if uid > 0xFFFFFFFF or uid in occupied:
            raise ValueError('external collision allocation is not free')
        remap[identity] = uid
    results, changes = {}, []
    for xy, data in sorted(outputs.items()):
        tile, out = Tile(data), bytearray(data)
        for kind, field in ((0, 'mddf'), (1, 'modf')):
            for j, (name, raw) in enumerate(tile.placements[kind]):
                identity = kind, _name_key(name), raw[4:]
                if identity in remap:
                    new_uid = remap[identity]
                    struct.pack_into('<I', out, tile.offsets[field] + 8 + j * (36, 64)[kind] + 4, new_uid)
                    changes.append(dict(tile=xy, kind=field, old_uid=u32(raw, 4), new_uid=new_uid,
                                        name=name.decode('latin1'), before_hex=raw[4:].hex(),
                                        after_hex=(struct.pack('<I', new_uid) + raw[8:]).hex()))
        results[xy] = bytes(out)
    return results, changes, dict(identity_count=len(ordered), identities_sha256=evidence_hash)


def tile_path(root, side, xy):
    return root / side / 'World/Maps/Azeroth' / ('Azeroth_%d_%d.adt' % xy)


def heights(cell):
    p, end = Tile.sub(cell, 0x1C, b'TVCM')
    if end - p != 588:
        raise ValueError('expected 145 MCVT vertices')
    base = struct.unpack_from('<f', cell, 0x78)[0]
    return tuple(h + base for h in struct.unpack_from('<145f', cell, p + 8))


def seam_regressions(errors):
    """Compare corresponding vertices, never let an old crack hide a new one."""
    return [j for j, (native, source, candidate) in enumerate(zip(
        errors['335'], errors['turtle'], errors['candidate']))
        if candidate > max(native, source) + 0.001]


def border_report(root, selection, candidates):
    """Every internal/external edge, including native neighbors outside 24 tiles."""
    tiles = {}

    def get(side, xy):
        key = side, xy
        if key not in tiles:
            p = tile_path(root, side, xy)
            tiles[key] = Tile(p.read_bytes()) if p.exists() else None
        return tiles[key]

    def cell(side, gx, gy):
        xy, slot = (gx // 16, gy // 16), (gy % 16) * 16 + gx % 16
        t = candidates.get(xy) if side == 'candidate' else None
        t = t or get('335' if side == 'candidate' else side, xy)
        return t.cells[slot] if t else None

    edges, missing, regressions, inherited, worst = 0, [], [], 0, 0.0
    seen = set()
    for tx, ty in selection:
        for i in range(256):
            gx, gy = tx * 16 + i % 16, ty * 16 + i // 16
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = (gx, gy), (gx + dx, gy + dy)
                edge = tuple(sorted((a, b)))
                if edge in seen:
                    continue
                seen.add(edge)
                a, b = edge
                horizontal = a[1] == b[1]
                ai = [r * 17 + 8 for r in range(9)] if horizontal else list(range(136, 145))
                bi = [r * 17 for r in range(9)] if horizontal else list(range(9))
                errors = {}
                for side in ('335', 'turtle', 'candidate'):
                    ca, cb = cell(side, *a), cell(side, *b)
                    if ca is None or cb is None:
                        break
                    ha, hb = heights(ca), heights(cb)
                    errors[side] = [abs(ha[x] - hb[y]) for x, y in zip(ai, bi)]
                if len(errors) != 3:
                    missing.append(edge)
                    continue
                edges += 1
                error = max(errors['candidate'])
                worst = max(worst, error)
                inherited += error > 0.001
                vertices = seam_regressions(errors)
                if vertices:
                    regressions.append({'edge': edge, 'vertices': vertices, 'errors': errors})
    return dict(edges=edges, unavailable_baselines=len(missing), unavailable_edges=missing,
                edges_over_1mm=inherited, max_error=worst, regressions=regressions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--research', type=Path, default=Path('work/elf-map-audit-research'))
    parser.add_argument('--output', type=Path, default=Path('work/high-elf-terrain-final'))
    parser.add_argument('--selection', type=Path, default=SELECTION)
    parser.add_argument('--native-client', type=Path, default=Path('/home/dev/wow-335'))
    parser.add_argument('--source-client', type=Path, default=Path('/home/dev/wow-turtle'))
    parser.add_argument('--audit-only', action='store_true', help='audit fresh map0 snapshots without emitting ADTs')
    args = parser.parse_args()
    plan, selection = load_plan(args.selection)
    if digest(AREA_MAP.read_bytes()) != plan['area_map_sha256']:
        raise ValueError('area map hash changed')
    area_map = {int(k): v for k, v in json.loads(AREA_MAP.read_text())['area_ids'].items()}
    inputs = load_inputs(args.research, plan)
    wdt = args.research / '335/World/Maps/Azeroth/Azeroth.wdt'
    wdt_before = wdt.read_bytes()
    if digest(wdt_before) != plan['native_wdt_sha256']:
        raise ValueError('native WDT hash changed')
    args.output.mkdir(parents=True, exist_ok=True)
    candidates, reports = {}, []
    outputs = compose_region(inputs, selection, area_map, source_model,
                             residuals=plan['residual_layers'])
    watched = {u32(raw, 4) for data in outputs.values() for records in Tile(data).placements
               for _, raw in records}
    audit, occupied, external = audit_map0(args.native_client, args.source_client,
                                         args.output / 'audit', inputs, watched, set(selection))
    (args.output / 'audit/map0-uids.json').write_text(json.dumps(audit, indent=2) + '\n')
    if args.audit_only:
        print(json.dumps({k: v for k, v in audit.items() if k not in
                          ('inventory', 'archive_priority', 'conflict_occurrences')}, indent=2))
        return
    if audit['content_sha256'] != plan['uid_audit']['content_sha256'] or (
            audit['occupied_uid_sha256'] != plan['uid_audit']['occupied_uid_sha256'] or
            audit['allocated_uid'] != plan['uid_audit']['allocated_uid']):
        raise ValueError('map0 audit changed; UID allocation must be reviewed')
    outputs, uid_changes = resolve_uids(outputs, plan['uid_resolutions'], audit['allocated_uid'], occupied)
    outputs, external_changes, external_plan = resolve_external_uids(
        outputs, external, inputs, occupied, audit['allocated_uid'])
    if external_plan != plan.get('external_uid_allocation'):
        raise ValueError('external UID allocation plan changed: ' + json.dumps(external_plan))
    uid_changes.extend(external_changes)
    final_uids = {}
    for xy, data in outputs.items():
        for kind, records in enumerate(Tile(data).placements):
            for name, raw in records:
                final_uids[u32(raw, 4)] = kind, _name_key(name), raw[4:]
    external_conflicts = [r for r in external if r['uid'] in final_uids and final_uids[r['uid']] !=
                          (r['kind'], _name_key(r['name'].encode('latin1')), bytes.fromhex(r['payload_hex']))]
    if external_conflicts:
        (args.output / 'audit/external-conflicts.json').write_text(json.dumps(external_conflicts, indent=2) + '\n')
        raise ValueError('%d UID occurrences conflict with unchanged native map0; see audit/external-conflicts.json' %
                         len(external_conflicts))
    (args.output / 'audit/external-conflicts.json').write_text('[]\n')
    for xy, result in outputs.items():
        selected = selection[xy]
        native, source = inputs[xy]
        tile = candidates[xy] = Tile(result)
        reports.append(dict(tile=xy, selected_source_cells=len(selected),
                            native_sha256=digest(native), source_sha256=digest(source),
                            output_sha256=digest(result), bytes=len(result),
                            placements=[len(p) for p in tile.placements],
                            mh2o_layers=sum(len(layers) for _, layers in liquid_cells(tile.body('mh2o')))))
    borders = border_report(args.research, selection, candidates)
    uid_conflicts = region_uid_conflicts(candidates)
    if uid_conflicts or borders['regressions']:
        raise ValueError('final terrain has UID conflicts or new border regressions')
    if wdt.read_bytes() != wdt_before:
        raise RuntimeError('native WDT changed during candidate generation')
    canonical = bytes.fromhex(plan['uid_resolutions']['canonical_payload_hex'])
    variant = bytes.fromhex(plan['uid_resolutions']['variant_payload_hex'])
    liquid_summary = dict(mh2o_authoritative_cells=0, legacy_only_cells=0, dual_active_cells=0,
                          multilayer_cells=0, mh2o_layers=0)
    for tile in candidates.values():
        for cell, (_, layers) in zip(tile.cells, liquid_cells(tile.body('mh2o'))):
            legacy = u32(cell, 0x6C) > 8
            liquid_summary['mh2o_authoritative_cells'] += bool(layers)
            liquid_summary['legacy_only_cells'] += legacy and not layers
            liquid_summary['dual_active_cells'] += legacy and bool(layers)
            liquid_summary['multilayer_cells'] += len(layers) > 1
            liquid_summary['mh2o_layers'] += len(layers)
    if liquid_summary['dual_active_cells']:
        raise ValueError('final terrain still has dual-active liquids')
    report = dict(status='offline_candidate_only', apply_ready=False,
                  terrain_ready=True,
                  tiles=reports, borders=borders,
                  region_uid_conflicts=uid_conflicts,
                  unchanged_native_uid_conflicts=external_conflicts,
                  uid_audit={k: v for k, v in audit.items() if k not in ('inventory', 'conflict_occurrences')},
                  external_uid_allocation=external_plan,
                  liquid_summary=liquid_summary,
                  adaptations=dict(removed_layers=plan['residual_layers'], uid_decisions=plan['uid_resolutions'],
                                   uid_changes=uid_changes, area_map=area_map,
                                   wmo_raw_delta=dict(changed_byte_offsets=[i + 4 for i, (a, b) in
                                                                           enumerate(zip(canonical, variant)) if a != b],
                                                      canonical_bounds=struct.unpack_from('<6f', canonical, 28),
                                                      variant_bounds=struct.unpack_from('<6f', variant, 28),
                                                      position_rotation_flags_sets_unchanged=True),
                                   materials='Unused MTEX/MTXF removed, no aliases. Surviving alpha bytes retained; MCLY/MCAL and predominant indices rebuilt.',
                                    liquids='Same-side MH2O layers authoritative; verified active MCLQ own size normalized before legacy flags0x3c and offset/size zero. Opaque payload retained; legacy-only cells unchanged.'),
                  native_wdt=dict(path=str(wdt), sha256=digest(wdt_before), byte_exact=True),
                  selection_sha256=digest(args.selection.read_bytes()),
                  area_map_sha256=digest(AREA_MAP.read_bytes()),
                  source_cells=sum(map(len, selection.values())),
                  limitations=['No client render/swimming/collision test or server extraction.',
                               'All MH2O layers preserved; current AzerothCore extractor reads only the first layer.',
                               'UID audit covers the specified native/source map0 snapshots, not arbitrary playing-client patches.',
                               'Asset conversion/namespace closure and DBC installation are separate outputs, not certified here.',
                               'Native MFBO retained tile-wide; no flight-boundary redesign.',
                               'Inherited source cracks are not repaired.'])
    for xy, result in outputs.items():
        (args.output / ('Azeroth_%d_%d.adt' % xy)).write_bytes(result)
    (args.output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(tiles=len(reports), source_cells=report['source_cells'],
                          checked_edges=borders['edges'],
                          unchecked_edges=borders['unavailable_baselines'],
                          new_seam_regressions=len(borders['regressions']),
                          region_uid_conflicts=len(uid_conflicts),
                          manifest=str(args.output / 'manifest.json')), indent=2))


if __name__ == '__main__':
    main()
