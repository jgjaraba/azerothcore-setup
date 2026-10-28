"""Structural ADT regressions; optional local fixtures never certify rendering.

Run: python3 -B -m unittest discover -s tools -p 'test_adt*.py' -v
Real inputs: work/elf-map-audit-research/{turtle,335}, and the six original
KarazhanCrypt tiles under work/extract/turtle/karazhancrypt. Missing fixtures
are explicitly skipped; no proprietary data is embedded or written by tests.
"""
import hashlib
import io
import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from adt import _adt_layout, _mhdr_offsets, parse_adt
from adt_convert import convert_adt
from adt_refs import placed_model_names


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'work/elf-map-audit-research'


def chunk(magic, body):
    return magic + struct.pack('<I', len(body)) + body


def walk(data):
    """Independent top-level framing check, including exact EOF coverage."""
    chunks = []
    pos = 0
    while pos < len(data):
        if pos + 8 > len(data):
            raise AssertionError('trailing partial chunk header')
        size = struct.unpack_from('<I', data, pos + 4)[0]
        end = pos + 8 + size
        if end > len(data):
            raise AssertionError('truncated chunk')
        chunks.append((pos, data[pos:end]))
        pos = end
    return chunks


def cells(data):
    base = 20 + struct.unpack_from('<I', data, 24)[0] + 8
    by_pos = dict(walk(data))
    result = []
    for i in range(256):
        off, size, flags, asyncid = struct.unpack_from('<4I', data, base + 16 * i)
        raw = by_pos[off] if off else None
        result.append((raw, size, flags, asyncid))
    return result


def fixture(legacy_size=False, optional=True):
    """Two adjacent MCNKs; zero internal MCLQ size as in real Vanilla ADTs."""
    out = bytearray(chunk(b'REVM', struct.pack('<I', 18)))
    out += chunk(b'RDHM', bytes(64))
    out += chunk(b'NICM', bytes(4096))
    values = [0] * 16
    values[0], values[1] = 3, 64
    # Reserved words deliberately look like invalid offsets; never follow them.
    values[12:] = [0xFFFFFFFF, 123, 456, 789]
    bodies = [(2, b'XETM', b'terrain.blp\0OBFM\0'),
              (3, b'XDMM', b'first.mdx\0second.mdx\0'),
              (4, b'DIMM', struct.pack('<3I', 10, 0, 10)),
              (7, b'FDDM', bytes(36))]
    if optional:
        bodies += [(9, b'OBFM', bytes(36)),
                   (10, b'O2HM', bytes(256 * 12)),
                   (11, b'FXTM', struct.pack('<I', 7))]
    for index, magic, body in bodies:
        values[index] = len(out) - 20
        out += chunk(magic, body)
    # Unknown chunks must survive, without treating reserved12 as MTCG.
    out += chunk(b'TSET', b'opaque extension')
    for slot in (0, 255):
        header = bytearray(128)
        struct.pack_into('<I', header, 0, 0x8000 | 4 | 8 | 16 | 32)
        struct.pack_into('<I', header, 0x34, 2040 + slot)
        water = (struct.pack('<2f', -2.5, 11.0) +
                 b''.join(struct.pack('<If', i * 7, i / 8.0) for i in range(81)) +
                 bytes([0x0F, 0x80, 0, 1, 2, 4, 0x40, 0x81]) * 8 + bytes(84))
        # MCLQ contains min/max, vertex depth/height, visibility/dark masks,
        # and opaque flow data. The legacy header itself declares zero bytes.
        liquid = b'QLCM' + bytes(4) + water
        struct.pack_into('<2I', header, 0x60, 136, len(liquid))
        raw = chunk(b'KNCM', header + liquid)
        struct.pack_into('<4I', out, 92 + slot * 16,
                         len(out), len(raw) - (8 if legacy_size else 0), 0x42, 99)
        out += raw
    struct.pack_into('<16I', out, 20, *values)
    return bytes(out)


class RoundtripChecks:
    def assert_roundtrip(self, source, area_map=None, model_map=None):
        out = convert_adt(source, area_map, model_map)
        old_chunks, new_chunks = walk(source), walk(out)
        self.assertEqual(len(old_chunks), len(new_chunks))
        self.assertEqual(new_chunks[2][0], 84)  # extractor contract
        for (old, _, flags, asyncid), (new, size, nf, na) in zip(cells(source), cells(out)):
            self.assertEqual((flags, asyncid), (nf, na))
            if old is None:
                self.assertIsNone(new)
                self.assertEqual(size, 0)
                continue
            self.assertEqual(new[:4], b'KNCM')
            self.assertEqual(size, len(new))
            expected = bytearray(old)
            if area_map:
                struct.pack_into('<I', expected, 0x3C,
                                 area_map(struct.unpack_from('<I', old, 0x3C)[0]))
            # Full-byte comparison includes all MCNK flags, liquid headers,
            # offsets, min/max, all heights, visibility masks and flow bytes.
            self.assertEqual(new, expected)
        unchanged = {b'REVM', b'OBFM', b'O2HM', b'FXTM', b'TSET',
                     b'XETM', b'OMWM', b'DIWM', b'FDDM', b'FDOM'}
        self.assertEqual([b for _, b in old_chunks if b[:4] in unchanged],
                         [b for _, b in new_chunks if b[:4] in unchanged])
        self.assertEqual(source[68:84], out[68:84])  # reserved words
        self.assertEqual(source[20:24], out[20:24])  # MHDR flags
        # Canonical output is stable, not just parseable by our own reader.
        self.assertEqual(convert_adt(out), out)
        _adt_layout(out)
        return out


class ConversionTests(RoundtripChecks, unittest.TestCase):
    def test_water_optional_chunks_flags_and_reserved_roundtrip(self):
        source = fixture()
        out = self.assert_roundtrip(source, lambda a: a + 100,
                                    lambda n: n.replace('.mdx', '.m2'))
        for index, magic in ((9, b'OBFM'), (10, b'O2HM'), (11, b'FXTM')):
            pos = 20 + struct.unpack_from('<I', out, 20 + index * 4)[0]
            self.assertEqual(out[pos:pos + 4], magic)
        self.assertEqual(placed_model_names(out), [b'second.m2'])
        with patch('builtins.open', return_value=io.BytesIO(out)):
            parsed = parse_adt('synthetic.adt')
        self.assertTrue(parsed['mfbo'])
        self.assertEqual(parsed['area_ids'][0], 2140)

    def test_legacy_mcin_payload_size_and_no_invented_mh2o(self):
        out = self.assert_roundtrip(fixture(legacy_size=True, optional=False))
        self.assertEqual(struct.unpack_from('<I', out, 60)[0], 0)
        self.assertNotIn(b'O2HM', [b[:4] for _, b in walk(out)])
        with patch('builtins.open', return_value=io.BytesIO(out)):
            self.assertFalse(parse_adt('synthetic.adt')['mfbo'])

    def test_dry_legacy_liquid_sentinels_preserved(self):
        for liquid in (0, 0xFFFFFFFF):
            source = bytearray(fixture())
            off = struct.unpack_from('<I', source, 92)[0]
            struct.pack_into('<2I', source, off + 0x68, liquid, 8)
            self.assert_roundtrip(bytes(source))

    def test_reject_malformed_framing_and_references(self):
        original = fixture()
        off = struct.unpack_from('<I', original, 92)[0]
        mutations = [
            (0, b'FAKE'), (8, struct.pack('<I', 17)),
            (16, struct.pack('<I', 60)),
            (24, struct.pack('<I', 0)),
            (24, struct.pack('<I', 65)),  # pointer inside a chunk
            (56, struct.pack('<I', 64)),  # MFBO points at MCIN
            (60, struct.pack('<I', len(original))),
            (88, struct.pack('<I', 4095)),
            (92, struct.pack('<I', off + 1)),
            (96, struct.pack('<I', 1)),
            (92, bytes(4)), (96, bytes(4)),
            (off, b'FAKE'), (off + 4, struct.pack('<I', 120)),
            (off + 4, struct.pack('<I', len(original))),
            (off + 0x68, struct.pack('<I', 137)),
            (off + 0x68, bytes(4)),
            (off + 0x6C, struct.pack('<I', len(original))),
            (off + 136, b'FAKE'),
            (92 + 16, struct.pack('<4I', off, 948, 0, 0)),
        ]
        for pos, replacement in mutations:
            data = original[:pos] + replacement + original[pos + len(replacement):]
            with self.subTest(pos=pos, replacement=replacement):
                for reader in (convert_adt, _mhdr_offsets):
                    with self.assertRaises(ValueError):
                        reader(data)
        for data in (b'', original[:7], original[:-1], original + b'BAD'):
            with self.assertRaises(ValueError):
                convert_adt(data)

    def test_magic_embedded_in_payload_is_not_a_chunk_boundary(self):
        source = bytearray(fixture())
        pos = source.index(b'OBFM')  # inside MTEX, before actual MFBO
        struct.pack_into('<I', source, 56, pos - 20)
        with self.assertRaises(ValueError):
            convert_adt(source)


class RealFixtureTests(RoundtripChecks, unittest.TestCase):
    def test_elf_region_16_tiles_turtle_and_335(self):
        paths = [AUDIT / edition / 'World/Maps/Azeroth' / f'Azeroth_{x}_{y}.adt'
                 for edition in ('turtle', '335')
                 for x in range(36, 40) for y in range(22, 26)]
        if not all(p.is_file() for p in paths) or not (AUDIT / 'tiles.json').is_file():
            self.skipTest('16 matched elf-region tiles/audit manifest unavailable')
        evidence = {tuple(row['tile']): row for row in json.loads((AUDIT / 'tiles.json').read_text())}
        active = 0
        for p in paths:
            with self.subTest(path=str(p.relative_to(ROOT))):
                source = p.read_bytes()
                edition = p.relative_to(AUDIT).parts[0]
                x, y = map(int, p.stem.split('_')[1:])
                self.assertEqual(hashlib.sha256(source).hexdigest(),
                                 evidence[(x, y)][edition]['sha256'])
                out = self.assert_roundtrip(source, lambda a: a + 10000,
                                           lambda n: n[:-4] + '.m2' if n.lower().endswith('.mdx') else None)
                if edition == 'turtle':
                    self.assertEqual(bool(struct.unpack_from('<I', out, 60)[0]),
                                     bool(struct.unpack_from('<I', source, 60)[0]))
                    active += sum(struct.unpack_from('<I', b, 0x6C)[0] > 8
                                  for b, _, _, _ in cells(source) if b)
        self.assertGreater(active, 0)

    def test_crypt_six_original_tiles(self):
        folder = ROOT / 'work/extract/turtle/karazhancrypt'
        paths = [folder / f'karazhancrypt_{x}_{y}.adt'
                 for x in range(34, 37) for y in (52, 53)]
        if not all(p.is_file() for p in paths):
            self.skipTest('six original crypt fixtures unavailable')
        for p in paths:
            with self.subTest(path=p.name):
                self.assert_roundtrip(p.read_bytes(), lambda a: 5086,
                                      lambda n: n[:-4] + '.m2' if n.lower().endswith('.mdx') else None)


if __name__ == '__main__':
    unittest.main()
