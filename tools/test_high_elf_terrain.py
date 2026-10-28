#!/usr/bin/env python3
"""Synthetic contracts plus optional local 24-tile/border integration tests.

Run: python3 -m unittest discover -s tools -p test_high_elf_terrain.py -v
Real inputs are read-only; generating the candidate is a separate CLI command.
"""
import json
from pathlib import Path
import struct
import tempfile
import unittest

from adt_client import scan_mcnk, self_length_mclq
from adt import CHUNK_MAGIC, MHDR_FIELDS
from high_elf_terrain import (AREA_MAP, Tile, audit_map0, border_report, chunk, compose_adt,
                              compose_region, digest, heights, liquid_cells, load_inputs,
                              load_plan, region_uid_conflicts, remove_residual_layer,
                              replace_subchunk, resolve_external_uids, resolve_uids,
                              seam_regressions, source_model, u32)


def placement(uid, x, y, size=36, name=0):
    raw = bytearray(size)
    struct.pack_into('<2I3f3f', raw, 0, name, uid, (x + .5) * 100 / 3,
                     7.25, (y + .5) * 100 / 3, 12, 34, 56)
    if size == 36:
        struct.pack_into('<2H', raw, 32, 1024, 2)
    else:
        struct.pack_into('<6f4H', raw, 32, 1, 2, 3, 4, 5, 6, 1, 2, 3, 0)
    return bytes(raw)


def make_cell(slot, refs, marker):
    out = bytearray(chunk(b'KNCM', bytes(128)))
    struct.pack_into('<5I', out, 8, 0x800C, slot % 16, slot // 16, 1, len(refs[0]))
    struct.pack_into('<I', out, 0x3C, 100 + marker)
    struct.pack_into('<I', out, 0x40, len(refs[1]))
    struct.pack_into('<3f', out, 0x70, 1600 / 3 * 32 - slot // 16 * 100 / 3,
                     1600 / 3 * 32 - slot % 16 * 100 / 3, marker)

    def emit(field, magic, body):
        struct.pack_into('<I', out, field, len(out))
        out.extend(chunk(magic, body))

    emit(0x1C, b'TVCM', struct.pack('<145f', *([marker / 10] * 145)))
    emit(0x20, b'RNCM', bytes([marker]) * 435)
    out.extend(bytes(range(13)))  # Vanilla MCNR padding outside size
    emit(0x24, b'YLCM', struct.pack('<4I', 0, 0x100, 0, 30011))
    emit(0x28, b'FRCM', struct.pack('<%dI' % (len(refs[0]) + len(refs[1])),
                                  *(refs[0] + refs[1])))
    emit(0x2C, b'LACM', bytes([marker]) * 2048)
    struct.pack_into('<I', out, 0x30, 2056)
    emit(0x34, b'HSCM', bytes([marker]) * 512)
    struct.pack_into('<I', out, 0x38, 512)
    emit(0x60, b'ESCM', bytes([marker]) * 28)
    struct.pack_into('<I', out, 0x64, 1)
    emit(0x68, b'QLCM', bytes([marker]) * 804)
    struct.pack_into('<I', out, 0x6C, 812)
    # Real Vanilla files have a zero declared MCLQ size.
    struct.pack_into('<I', out, u32(out, 0x68) + 4, 0)
    emit(0x7C, b'VCCM', bytes([marker]) * 580)
    struct.pack_into('<I', out, 4, len(out) - 8)
    return bytes(out)


def make_liquid(specs):
    """Independent fixture writer: reserve all records before referenced data."""
    body = bytearray(3072)
    offsets = {}
    for slot, (_, layers) in specs.items():
        offsets[slot] = len(body)
        body.extend(bytes(len(layers) * 24))
    for slot, (attr, layers) in specs.items():
        a = len(body) if attr else 0
        body.extend(attr)
        struct.pack_into('<3I', body, slot * 12, offsets[slot] if layers else 0, len(layers), a)
        for j, (lvf, rect, mask, vertices) in enumerate(layers):
            mp = len(body) if mask else 0
            body.extend(mask)
            vp = len(body) if vertices else 0
            body.extend(vertices)
            struct.pack_into('<2H2f4B2I', body, offsets[slot] + j * 24,
                             5, lvf, 1.25, 9.5, *rect, mp, vp)
    return bytes(body)


def make_tile(marker=1, models=(), wmos=(), refs=None, liquid=None,
              model_names=(b'first.m2',), model_ids=None, texture=b'native.blp',
              texture_flags=None):
    refs = refs or {}
    bodies = dict(mtex=texture + b'\0', mmdx=b'\0'.join(model_names) + b'\0',
                  mmid=struct.pack('<I', 0) if model_ids is None else model_ids,
                  mwmo=b'building.wmo\0', mwid=struct.pack('<I', 0),
                  mddf=b''.join(models), modf=b''.join(wmos))
    if liquid is not None:
        bodies['mh2o'] = liquid
    if texture_flags is not None:
        bodies['mtxf'] = struct.pack('<I', texture_flags)
    out = bytearray(chunk(b'REVM', struct.pack('<I', 18)) + chunk(b'RDHM', bytes(64)) +
                    chunk(b'NICM', bytes(4096)))
    header = [0] * 16
    header[1] = 64
    header[12:] = [0xFFFFFFFF, 7, 9, 123]
    for key, body in bodies.items():
        header[MHDR_FIELDS.index(key)] = len(out) - 20
        out.extend(chunk(CHUNK_MAGIC[key], body))
    out.extend(chunk(b'ZZZZ', b'opaque native payload' + bytes([marker])))
    for i in range(256):
        cell = make_cell(i, refs.get(i, ([], [])), marker)
        struct.pack_into('<4I', out, 92 + i * 16, len(out), len(cell), 17, 23)
        out.extend(cell)
    struct.pack_into('<16I', out, 20, *header)
    return bytes(out)


def invariant_cell(cell, material_adaptation=False):
    """Strip exactly the permitted differences, keep every other terrain byte."""
    # Only MCLQ's own size may differ: require its precise, verified extent.
    # Active source headers may be zero; inactive output must be self-length.
    cell = bytearray(self_length_mclq(cell))
    for tag, p, end in scan_mcnk(cell):
        if tag == b'QLCM':
            if u32(cell, p + 4) != end - p - 8:
                raise AssertionError('MCLQ must have its exact payload size')
            struct.pack_into('<I', cell, p + 4, 0)
    data = bytearray(cell)
    struct.pack_into('<I', data, 8, u32(data, 8) & ~0x3C)
    if u32(data, 0x24):
        p, _ = Tile.sub(data, 0x24, b'YLCM')
        for i in range(u32(data, 0x14)):
            struct.pack_into('<I', data, p + 8 + i * 16, 0)
    if u32(data, 0x28):
        p, end = Tile.sub(data, 0x28, b'FRCM')
        del data[p:end]
    if material_adaptation:
        # Delete by original offsets before slicing; indices change only after
        # the header. These blocks are tested semantically/byte-wise below.
        data = bytearray(cell)
        parts = [Tile.sub(cell, field, magic) for field, magic in
                 ((0x24, b'YLCM'), (0x2C, b'LACM'), (0x28, b'FRCM'))]
        for p, end in sorted(parts, reverse=True):
            del data[p:end]
        for field in (0x14, 0x30):
            struct.pack_into('<I', data, field, 0)
        data[0x48:0x58] = bytes(16)
        struct.pack_into('<I', data, 8, u32(data, 8) & ~0x3C)
    for field in (4, 0x18, 0x1C, 0x20, 0x24, 0x28, 0x2C, 0x34,
                  0x3C, 0x40, 0x60, 0x68, 0x6C, 0x7C):
        struct.pack_into('<I', data, field, 0)
    return bytes(data)


def identities(tile, kind):
    return [(name.lower().replace(b'/', b'\\'), raw[4:])
            for name, raw in tile.placements[kind]]


class SyntheticTests(unittest.TestCase):
    def test_mclq_self_length_is_only_four_bytes_and_opaque(self):
        for declared in (0, 1, 804, 0xFFFFFFFF):
            cell = bytearray(make_cell(0, ([], []), 1))
            p = u32(cell, 0x68)
            struct.pack_into('<I', cell, p + 4, declared)
            # An apparent FOURCC inside water is data, never a boundary.
            cell[p + 24:p + 32] = chunk(b'VCCM', b'')
            out = self_length_mclq(bytes(cell))
            self.assertEqual(out[:p + 4], cell[:p + 4])
            self.assertEqual(out[p + 8:], cell[p + 8:])
            self.assertEqual(u32(out, p + 4), 804)
            inactive = bytearray(out)
            struct.pack_into('<2I', inactive, 0x68, 0, 0)
            self.assertEqual(self_length_mclq(bytes(inactive)), inactive)
            self.assertEqual(scan_mcnk(inactive)[-1][0], b'VCCM')

    def test_scanner_rejects_old_deactivation_overruns_and_overlap(self):
        original = make_cell(0, ([], []), 1)
        old = bytearray(original)
        struct.pack_into('<2I', old, 0x68, 0, 0)
        with self.assertRaisesRegex(ValueError, 'unknown MCNK tag'):
            scan_mcnk(old)
        for size in (len(original), u32(original, 0x6C) + 4):
            bad = bytearray(original)
            struct.pack_into('<I', bad, 0x6C, size)
            with self.assertRaisesRegex(ValueError, 'exceeds cell|overlaps'):
                self_length_mclq(bad)
        dry = bytearray(self_length_mclq(original))
        struct.pack_into('<2I', dry, 0x68, 0xFFFFFFFF, 8)
        self.assertEqual(self_length_mclq(bytes(dry)), dry)
        self.assertEqual(scan_mcnk(dry)[-1][0], b'VCCM')
        bad_alpha = bytearray(original)
        struct.pack_into('<I', bad_alpha, 0x30, 2048)
        with self.assertRaisesRegex(ValueError, 'MCAL'):
            scan_mcnk(bad_alpha)

    def test_objects_owned_by_refs_and_no_boundary_resurrection(self):
        # A native-only ruin anchored in replaced cell0 overlaps native cell1.
        # A native-only addition in cell1 must remain. UID10 is shared.
        native = make_tile(models=[placement(10, 0, 0), placement(11, 0, 0),
                                   placement(12, 1, 0), placement(13, 2, 0)],
                           wmos=[placement(20, 0, 0, 64), placement(21, 1, 0, 64)],
                           refs={0: ([0, 1], [0]), 1: ([0, 1, 2], [0, 1])})
        source = make_tile(2, models=[placement(10, 0, 0), placement(14, 0, 0),
                                             placement(15, 1, 0)],
                           wmos=[placement(22, 0, 0, 64)],
                           refs={0: ([0, 1, 2], [0]), 1: ([0, 1, 2], [0])},
                           model_names=(b'first.mdx',), texture=b'source.blp')
        result = Tile(compose_adt(native, source, {0}, {102: 999},
                                  lambda n: n.replace('.mdx', '.m2'),
                                  lambda n: 'longer\\new_' + n))
        self.assertEqual([u32(r, 4) for _, r in result.placements[0]], [12, 13, 10, 14])
        self.assertEqual([u32(r, 4) for _, r in result.placements[1]], [21, 22])
        self.assertEqual(result.refs[0], ([2, 3], [1]))
        self.assertEqual(result.refs[1], ([2, 0], [0]))
        self.assertEqual(u32(result.cells[0], 0x3C), 999)
        self.assertEqual(u32(result.cells[1], 0x3C), 101)
        self.assertEqual(result.placements[1][1][0], b'longer\\new_building.wmo')
        for side, slot in ((source, 0), (native, 1)):
            self.assertEqual(invariant_cell(result.cells[slot]), invariant_cell(Tile(side).cells[slot]))

    def test_owner_fallback_uses_nearest_reference_not_first(self):
        # Anchor isn't in its reference set. Nearest ref1 owns the object,
        # despite an overlap in selected ref0.
        native = make_tile(models=[placement(77, 2, 0)], refs={0: ([0], []), 1: ([0], [])})
        source = make_tile(2)
        result = Tile(compose_adt(native, source, {0}))
        self.assertEqual(len(result.placements[0]), 1)
        self.assertEqual(result.refs[1], ([0], []))

    def test_region_owner_prevents_reappearance_across_tile_boundary(self):
        replaced, retained = placement(90, 0, 15), placement(91, 1, 15)
        inputs = {
            (0, 0): (make_tile(models=[replaced, retained],
                               refs={240: ([0], []), 241: ([1], [])}), make_tile(2)),
            (0, 1): (make_tile(models=[replaced, retained],
                               refs={0: ([0], []), 1: ([1], [])}), make_tile(2))}
        outputs = compose_region(inputs, {(0, 0): {240}, (0, 1): set()})
        for data in outputs.values():
            self.assertEqual([u32(raw, 4) for _, raw in Tile(data).placements[0]], [91])
        self.assertEqual(Tile(outputs[(0, 1)]).refs[0], ([], []))
        self.assertEqual(Tile(outputs[(0, 1)]).refs[1], ([0], []))

    def test_liquid_all_layers_offsets_formats_and_legacy_preserved(self):
        native_liquid = make_liquid({0: (b'N' * 16, [(0, (0, 0, 2, 3), b'\x35', b'H' * 60)]),
                                     1: (b'', [(2, (0, 0, 8, 8), b'', b'D' * 81)]),
                                     2: (b'A' * 16, [])})
        source_liquid = make_liquid({0: (b'S' * 16, [(1, (2, 3, 2, 2), b'\x03', b'U' * 72),
                                                   (0, (0, 0, 1, 1), b'', b''),
                                                   (2, (0, 0, 8, 8), b'B' * 8, b'D' * 81)])})
        native = make_tile(liquid=native_liquid)
        source = make_tile(2, liquid=source_liquid)
        out = Tile(compose_adt(native, source, {0}))
        expected = liquid_cells(native_liquid)
        expected[0] = liquid_cells(source_liquid)[0]
        self.assertEqual(liquid_cells(out.body('mh2o')), expected)
        for slot, original in ((0, Tile(source)), (1, Tile(native))):
            cell, old = out.cells[slot], original.cells[slot]
            self.assertEqual(u32(cell, 8), u32(old, 8) & ~0x3C)
            self.assertEqual(struct.unpack_from('<2I', cell, 0x68), (0, 0))
            p, q = cell.index(b'QLCM', 136), u32(old, 0x68)
            self.assertEqual(u32(cell, p + 4), u32(old, 0x6C) - 8)
            self.assertEqual(cell[p:p + 4], old[q:q + 4])
            self.assertEqual(cell[p + 8:p + u32(old, 0x6C)], old[q + 8:q + u32(old, 0x6C)])
        # An MH2O chunk/attributes without layers does not suppress legacy.
        self.assertEqual(out.cells[2][8:12], Tile(native).cells[2][8:12])
        self.assertGreater(u32(out.cells[2], 0x6C), 8)
        # Check every serialized instance directly, independently of the parser.
        body = out.body('mh2o')
        p, count, attr = struct.unpack_from('<3I', body, 0)
        self.assertEqual(count, 3)
        self.assertEqual(body[attr:attr + 16], b'S' * 16)
        for j, size, mask, vertices in ((0, 72, b'\x03', b'U' * 72),
                                        (1, 0, b'', b''), (2, 81, b'B' * 8, b'D' * 81)):
            mp, vp = struct.unpack_from('<2I', body, p + j * 24 + 16)
            self.assertEqual(body[mp:mp + len(mask)] if mp else b'', mask)
            self.assertEqual(body[vp:vp + size] if vp else b'', vertices)
        # Selecting legacy-only water clears the native MH2O slot, not MCLQ.
        out = Tile(compose_adt(native, make_tile(2), {0}))
        self.assertEqual(liquid_cells(out.body('mh2o'))[0], (b'', []))

    def test_material_flags_name_offsets_and_full_empty_selection(self):
        native = make_tile(texture_flags=1)
        # MMID order is deliberately repeated and nonsequential.
        names = (b'unused.mdx', b'chosen_long_name.mdx')
        source = make_tile(2, models=[placement(30, 0, 0, name=0), placement(31, 0, 0, name=2)],
                           refs={0: ([0, 1], [])}, model_names=names,
                           model_ids=struct.pack('<3I', len(names[0]) + 1, 0, len(names[0]) + 1),
                           texture_flags=2)
        out = Tile(compose_adt(native, source, {0}, model_map=lambda n: n.replace('.mdx', '.m2')))
        self.assertEqual(out.textures, [b'native.blp', b'native.blp'])
        self.assertEqual(out.body('mtxf'), struct.pack('<2I', 1, 2))
        self.assertEqual([n for n, _ in out.placements[0]], [b'chosen_long_name.m2'] * 2)
        p, _ = Tile.sub(out.cells[0], 0x24, b'YLCM')
        self.assertEqual(u32(out.cells[0], p + 8), 1)
        for selection, original in ((set(), native), (set(range(256)), source)):
            result, before = Tile(compose_adt(native, source, selection)), Tile(original)
            for i in range(256):
                self.assertEqual(invariant_cell(result.cells[i]), invariant_cell(before.cells[i]))
            self.assertEqual(result.header[12:], Tile(native).header[12:])
            self.assertIn(b'opaque native payload\x01', result.data)

    def test_collisions_invalid_references_and_liquid_offsets_fail(self):
        native = make_tile(models=[placement(5, 1, 0)], refs={1: ([0], [])})
        source = make_tile(2, models=[placement(5, 0, 0)], refs={0: ([0], [])})
        with self.assertRaisesRegex(ValueError, 'UID'):
            compose_adt(native, source, {0})
        cross_kind = make_tile(2, wmos=[placement(5, 0, 0, 64)], refs={0: ([], [0])})
        with self.assertRaisesRegex(ValueError, 'MDDF and MODF'):
            compose_adt(native, cross_kind, {0})
        cross_region = {(0, 0): Tile(native), (0, 1): Tile(cross_kind)}
        self.assertEqual(region_uid_conflicts(cross_region)[0]['uid'], 5)
        with self.assertRaisesRegex(ValueError, 'MCRF placement'):
            compose_adt(make_tile(refs={0: ([12], [])}), make_tile(), {0})
        for selected in ({256}, {-1}, {True}, {'1'}):
            with self.assertRaises(ValueError):
                compose_adt(native, source, selected)
        bad = bytearray(3072)
        struct.pack_into('<3I', bad, 0, 3072, 1, 0)
        with self.assertRaisesRegex(ValueError, 'MH2O'):
            compose_adt(make_tile(liquid=bytes(bad)), make_tile(), {0})

    def test_old_large_crack_cannot_mask_new_crack_at_different_vertex(self):
        errors = {'335': [10, 0, 0, 0, 0, 0, 0, 0, 0],
                  'turtle': [10, 0, 0, 0, 0, 0, 0, 0, 0],
                  'candidate': [10, 5, 0, 0, 0, 0, 0, 0, 0]}
        self.assertEqual(seam_regressions(errors), [1])

    def test_dry_liquid_sentinel_and_vanilla_texture_id_are_not_relocated(self):
        native = bytearray(make_tile(models=[placement(70, 0, 0)],
                                     refs={0: ([0], []), 1: ([0], [])}))
        original = Tile(bytes(native))
        p = original.entries[1][0]
        struct.pack_into('<2I', native, p + 0x68, 0xFFFFFFFF, 8)
        struct.pack_into('<I', native, p + u32(original.cells[1], 0x68) + 4, 804)
        struct.pack_into('<I', native, p + 0x7C, 0x12345678)
        # Replaced owner0 drops ref1, shifting later payloads by four bytes.
        cell = Tile(compose_adt(bytes(native), make_tile(2), {0})).cells[1]
        self.assertEqual(len(cell), len(original.cells[1]) - 4)
        self.assertEqual(u32(cell, 0x68), 0xFFFFFFFF)
        self.assertEqual(u32(cell, 0x6C), 8)
        self.assertEqual(u32(cell, 0x7C), 0x12345678)

    def test_residual_layer_rebuild_preserves_survivors_and_reindexes_predominant(self):
        cell = make_cell(0, ([], []), 1)
        layers = b''.join(struct.pack('<4I', i, 0x100 if i else 0, max(0, i - 1) * 2048, i)
                          for i in range(4))
        cell = replace_subchunk(cell, 0x24, b'YLCM', layers)
        cell = replace_subchunk(cell, 0x2C, b'LACM', bytes(2048) + b'\xAB' * 2048 + b'\xCD' * 2048)
        cell = bytearray(cell)
        struct.pack_into('<I', cell, 0x14, 4)
        struct.pack_into('<I', cell, 0x30, 6152)
        cell[0x48:0x58] = b'\xE0' * 16  # old predominant indices0,0,2,3
        rule = dict(layer=1, texture='error_1.blp', alpha_sha256=digest(bytes(2048)),
                    effective_nonzero_samples=0, effective_percent=0)
        out = remove_residual_layer(bytes(cell), [b'a', b'error_1.blp', b'b', b'c'], rule)
        self.assertEqual(u32(out, 0x14), 3)
        self.assertEqual(u32(out, 0x30), 4104)
        self.assertEqual(out[0x48:0x58], b'\x90' * 16)
        ap, ae = Tile.sub(out, 0x2C, b'LACM')
        self.assertEqual(out[ap + 8:ae], b'\xAB' * 2048 + b'\xCD' * 2048)
        lp, le = Tile.sub(out, 0x24, b'YLCM')
        self.assertEqual([struct.unpack_from('<4I', out, p) for p in range(lp + 8, le, 16)],
                         [(0, 0, 0, 0), (2, 0x100, 0, 2), (3, 0x100, 2048, 3)])
        self.assertEqual(invariant_cell(out, True), invariant_cell(bytes(cell), True))
        with self.assertRaisesRegex(ValueError, 'hash'):
            remove_residual_layer(bytes(cell), [b'a', b'error_1.blp', b'b', b'c'],
                                  dict(rule, alpha_sha256='wrong'))

    def test_external_uid_allocator_changes_only_uid_and_reuses_identity_across_tiles(self):
        raw = placement(100, 0, 0)
        outputs = {(0, 0): make_tile(models=[raw], refs={0: ([0], [])}),
                   (0, 1): make_tile(models=[raw], refs={0: ([0], [])})}
        external = [dict(uid=100, kind=0, name='different.m2', payload_hex=placement(100, 9, 9)[4:].hex())]
        inputs = {xy: (make_tile(), make_tile(2)) for xy in outputs}
        out, changes, evidence = resolve_external_uids(outputs, external, inputs, {100, 999}, 1000)
        self.assertEqual(evidence['identity_count'], 1)
        for data in out.values():
            record = Tile(data).placements[0][0][1]
            self.assertEqual(u32(record, 4), 1001)
            self.assertEqual(record[8:], raw[8:])
        self.assertEqual(len(changes), 2)
        with self.assertRaisesRegex(ValueError, 'not free'):
            resolve_external_uids(outputs, external, inputs, {1001}, 1000)


RESEARCH = Path(__file__).resolve().parents[1] / 'work/elf-map-audit-research'


@unittest.skipUnless((RESEARCH / '335').exists() and Path('/home/dev/wow-335').exists(),
                     'local research/client snapshots absent')
class RealTilesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan, cls.selection = load_plan()
        cls.candidates = {}
        cls.inputs = {}
        inputs = load_inputs(RESEARCH, cls.plan)
        cls.areas = {int(k): v for k, v in json.loads(AREA_MAP.read_text())['area_ids'].items()}
        outputs = compose_region(inputs, cls.selection, cls.areas, source_model,
                                 residuals=cls.plan['residual_layers'])
        watched = {u32(raw, 4) for data in outputs.values() for records in Tile(data).placements
                   for _, raw in records}
        with tempfile.TemporaryDirectory(dir='/tmp/opencode') as tmp:
            cls.audit, cls.occupied, cls.external = audit_map0(
                Path('/home/dev/wow-335'), Path('/home/dev/wow-turtle'), Path(tmp),
                inputs, watched, set(cls.selection))
        outputs, cls.uid_changes = resolve_uids(outputs, cls.plan['uid_resolutions'],
                                                cls.audit['allocated_uid'], cls.occupied)
        outputs, extra, cls.external_plan = resolve_external_uids(
            outputs, cls.external, inputs, cls.occupied, cls.audit['allocated_uid'])
        cls.uid_changes.extend(extra)
        cls.payload_remap = {(0 if c['kind'] == 'mddf' else 1,
                              c['name'].lower().replace('/', '\\').encode('latin1'),
                              bytes.fromhex(c['before_hex'])): bytes.fromhex(c['after_hex'])
                             for c in cls.uid_changes}
        for xy, result in outputs.items():
            native, source = inputs[xy]
            cls.candidates[xy] = Tile(result)
            cls.inputs[xy] = (Tile(native), Tile(source))

    def test_24_tiles_all_6144_cells_exact_terrain_materials_and_liquids(self):
        self.assertEqual(len(self.candidates), 24)
        self.assertEqual(sum(map(len, self.selection.values())), 3899)
        multilayer = 0
        for xy, out in self.candidates.items():
            native, source = self.inputs[xy]
            liquids = [liquid_cells(t.body('mh2o')) for t in (native, source)]
            result_liquids = liquid_cells(out.body('mh2o'))
            for i, cell in enumerate(out.cells):
                with self.subTest(tile=xy, slot=i):
                    side = int(i in self.selection[xy])
                    before = (native, source)[side]
                    old = before.cells[i]
                    scan_mcnk(cell)
                    if result_liquids[i][1] and u32(old, 0x6C) > 8:
                        old_p = u32(old, 0x68)
                        blocks = [b for b in scan_mcnk(cell) if b[0] == b'QLCM']
                        self.assertEqual(len(blocks), 1)
                        _, p, end = blocks[0]
                        self.assertEqual(u32(cell, p + 4), u32(old, 0x6C) - 8)
                        self.assertEqual(cell[p + 8:end], old[old_p + 8:old_p + u32(old, 0x6C)])
                    residual = next((r for r in self.plan['residual_layers']
                                     if tuple(r['tile']) == xy and r['slot'] == i), None)
                    self.assertEqual(invariant_cell(cell, bool(residual)), invariant_cell(old, bool(residual)))
                    self.assertEqual(heights(cell), heights(old))
                    expected_area = self.areas.get(u32(old, 0x3C), u32(old, 0x3C)) if side else u32(old, 0x3C)
                    self.assertEqual(u32(cell, 0x3C), expected_area)
                    self.assertEqual(result_liquids[i], liquids[side][i])
                    if result_liquids[i][1]:
                        self.assertEqual(u32(cell, 8), u32(old, 8) & ~0x3C)
                        self.assertEqual(struct.unpack_from('<2I', cell, 0x68), (0, 0))
                    else:
                        self.assertEqual(u32(cell, 8), u32(old, 8))
                        self.assertEqual(u32(cell, 0x6C), u32(old, 0x6C))
                        old_lq = [old[p:end] for tag, p, end in scan_mcnk(old) if tag == b'QLCM']
                        new_lq = [cell[p:end] for tag, p, end in scan_mcnk(cell) if tag == b'QLCM']
                        self.assertEqual(new_lq, old_lq)
                    multilayer += len(result_liquids[i][1]) > 1
                    lp, _ = Tile.sub(cell, 0x24, b'YLCM')
                    op, _ = Tile.sub(old, 0x24, b'YLCM')
                    surviving = [j for j in range(u32(old, 0x14)) if not residual or j != residual['layer']]
                    self.assertEqual(u32(cell, 0x14), len(surviving))
                    for j, old_j in enumerate(surviving):
                        self.assertEqual(out.textures[u32(cell, lp + 8 + j * 16)].lower().replace(b'/', b'\\'),
                                         before.textures[u32(old, op + 8 + old_j * 16)].lower().replace(b'/', b'\\'))
                        self.assertEqual(cell[lp + 12 + j * 16:lp + 16 + j * 16],
                                         old[op + 12 + old_j * 16:op + 16 + old_j * 16])
                    if residual:
                        ap, ae = Tile.sub(cell, 0x2C, b'LACM')
                        old_ap, _ = Tile.sub(old, 0x2C, b'LACM')
                        kept = [old_j for old_j in surviving if old_j]
                        expected_alpha = b''.join(old[old_ap + 8 + (j - 1) * 2048:
                                                       old_ap + 8 + j * 2048] for j in kept)
                        self.assertEqual(cell[ap + 8:ae], expected_alpha)
                        self.assertEqual([u32(cell, lp + 16 + j * 16) for j in range(len(surviving))],
                                         [0, 0, 2048])
                    for field, magic in ((0x1C, b'TVCM'), (0x20, b'RNCM'), (0x2C, b'LACM'),
                                         (0x34, b'HSCM'), (0x60, b'ESCM'), (0x68, b'QLCM')):
                        p, q = u32(cell, field), u32(old, field)
                        if q and q < len(old) and not (field == 0x68 and result_liquids[i][1]):
                            self.assertEqual(cell[p:p + 4], old[q:q + 4])
                            self.assertEqual(cell[p:p + 4], magic)
            for kind in range(2):
                output_ids = identities(out, kind)
                self.assertEqual(len(output_ids), len(set(output_ids)))
                self.assertEqual(len(output_ids), len({u32(raw, 4) for _, raw in out.placements[kind]}))
                # A cell may only reference original chosen-side identities,
                # retaining order and multiplicity, after owner filtering.
                for i in range(256):
                    side = int(i in self.selection[xy])
                    before = (native, source)[side]
                    old_ids = []
                    for name, raw in before.placements[kind]:
                        name = name.lower().replace(b'/', b'\\')
                        if side and kind == 0 and name.endswith(b'.mdx'):
                            name = name[:-4] + b'.m2'
                        old_ids.append((name, self.payload_remap.get((kind, name, raw[4:]), raw[4:])))
                    expected = [old_ids[r] for r in before.refs[i][kind] if old_ids[r] in output_ids]
                    self.assertEqual([output_ids[r] for r in out.refs[i][kind]], expected)
        self.assertEqual(multilayer, 8)

    def test_crash_7c3a42_retained_bytes_regression(self):
        # RESULTS.md: Azeroth_33_25 slot124, MCLQ at cell+1EFC. Before
        # normalization, the scanner walks water and reads C1C1C1C1 as a size
        # at +2194, leading to the next identifier read at 7C3A42.
        cell = self.candidates[(33, 25)].cells[124]
        tag, p, end = next(b for b in scan_mcnk(cell) if b[0] == b'QLCM')
        self.assertEqual(p, 0x1EFC)
        self.assertEqual(len(cell), 8752)
        self.assertEqual(u32(cell, 0x2194), 0xC1C1C1C1)
        self.assertEqual(struct.unpack_from('<2I', cell, 0x68), (0, 0))
        self.assertEqual(u32(cell, p + 4), end - p - 8)
        old = bytearray(cell)
        struct.pack_into('<I', old, p + 4, 0)
        with self.assertRaisesRegex(ValueError, 'unknown MCNK tag'):
            scan_mcnk(old)

    def test_map0_audit_uid_resolutions_and_no_unused_or_error_materials(self):
        self.assertEqual(self.audit['content_sha256'], self.plan['uid_audit']['content_sha256'])
        self.assertEqual(self.audit['occupied_uid_sha256'], self.plan['uid_audit']['occupied_uid_sha256'])
        self.assertEqual(self.external_plan, self.plan['external_uid_allocation'])
        self.assertEqual(self.audit['present_adts'], {'335': 709, 'turtle': 741})
        self.assertEqual(self.audit['allocated_uid'], 231311971)
        self.assertNotIn(231311971, self.occupied)
        self.assertEqual(region_uid_conflicts(self.candidates), [])
        final_ids = {}
        for out in self.candidates.values():
            used = set()
            for cell in out.cells:
                p, end = Tile.sub(cell, 0x24, b'YLCM')
                used.update(u32(cell, j) for j in range(p + 8, end, 16))
            self.assertEqual(used, set(range(len(out.textures))))
            self.assertFalse({b'error_1.blp', b'error_2.blp'} & set(out.textures))
            for kind, records in enumerate(out.placements):
                for name, raw in records:
                    uid = u32(raw, 4)
                    final_ids[uid] = (kind, name.lower().replace(b'/', b'\\'), raw[4:])
                    if uid == 164208:
                        self.assertEqual(raw[4:].hex(), self.plan['uid_resolutions']['canonical_payload_hex'])
        for item in self.external:
            if item['uid'] in final_ids:
                self.assertEqual(final_ids[item['uid']],
                                 (item['kind'], item['name'].lower().replace('/', '\\').encode('latin1'),
                                  bytes.fromhex(item['payload_hex'])))
        new_uids = set(final_ids) - self.occupied
        self.assertEqual(new_uids, set(range(231311971, 231313047)))
        for change in self.uid_changes:
            before, after = bytes.fromhex(change['before_hex']), bytes.fromhex(change['after_hex'])
            if change['old_uid'] != 164208:
                self.assertEqual(before[4:], after[4:])

    def test_known_replaced_native_decorations_cannot_return_in_neighbor(self):
        # These three records are referenced by native cells in37_26 but
        # owned by references in source-selected37_25. Local-only ownership
        # would incorrectly resurrect them in the extension tile.
        forbidden = {463701, 376904, 463679, 207110, 207072, 207075}
        for out in self.candidates.values():
            self.assertFalse(forbidden & {u32(raw, 4) for _, raw in out.placements[0]})

    def test_all_internal_tile_and_external_native_borders(self):
        report = border_report(RESEARCH, self.selection, self.candidates)
        self.assertGreater(report['edges'], 12000)
        # Both snapshots lack tile33_21. All 16 incident cells are native;
        # report the gap instead of claiming to have validated that boundary.
        self.assertEqual(report['unavailable_baselines'], 16)
        for a, b in report['unavailable_edges']:
            self.assertEqual(a[1], 351)
            self.assertEqual(b[1], 352)
            self.assertEqual(b[0] // 16, 33)
            self.assertNotIn(b[0] % 16, self.selection[(33, 22)])
        self.assertEqual(report['regressions'], [])


if __name__ == '__main__':
    unittest.main()
