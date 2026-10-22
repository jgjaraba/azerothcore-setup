#!/usr/bin/env python3
"""Vanilla 1.12 -> WotLK 3.3.5 ADT converter (full re-serializer).

This retains the sampled dry-pilot terrain chunks; it is not a validated
generic converter for wet/optional-chunk-bearing maps. The rewrite:
  1. remaps MMDX model names (e.g. `.mdx` -> `.m2`) via a model map,
  2. remaps MCNK area IDs via an area map,
and re-emits the file with recalculated MHDR offsets and MCIN entries.

Water conversion is NOT implemented. The optional MHDR field mapping below
has a known limitation; see docs/turtle-wow/compatibility.md before reuse.
"""
import struct
from adt_refs import remap_name_table

REVM = b'REVM'
RDHM = b'RDHM'
NICM = b'NICM'

CHUNK_MAGIC = {
    'mtex': b'XETM', 'mmdx': b'XDMM', 'mmid': b'DIMM', 'mwmo': b'OMWM',
    'mwid': b'DIWM', 'mddf': b'FDDM', 'modf': b'FDOM', 'mh2o': b'O2HM',
    'mfbo': b'OBFM', 'mtxf': b'FXTM', 'mtcg': b'GCTM',
}
# MHDR field index -> chunk key (index 0 = flags, 1 = mcin)
MHDR_FIELDS = ['flags', 'mcin', 'mtex', 'mmdx', 'mmid', 'mwmo', 'mwid',
               'mddf', 'modf', 'mh2o', 'mtxf', 'mtcg', 'mfbo', 'a13', 'a14', 'a15']

def _cstrs(data, off, end):
    out, p = [], off
    while p < end:
        e = data.find(b'\x00', p, end)
        if e == -1 or e == p:
            break
        out.append(data[p:e].decode('latin1', errors='replace'))
        p = e + 1
    return out

def _rebuild_cstr_chunk(magic, names):
    body = b''.join(n.encode('latin1', 'ignore') + b'\x00' for n in names)
    return magic + struct.pack('<I', len(body)) + body

def convert_adt(data, area_map=None, model_map=None):
    """data: bytes. area_map(aid)->aid. model_map(name)->name|None (keep)."""
    if data[:4] != REVM:
        raise ValueError('not an ADT')
    mhdr = data.find(RDHM, 0, 0x100)
    if mhdr == -1:
        raise ValueError('no MHDR')
    base = mhdr + 8
    vals = list(struct.unpack_from('<16I', data, base))

    mver = data[:mhdr]  # MVER chunk (magic+size+version)

    # Extract body chunks (raw magic+size+data) via MHDR offsets.
    chunks = {}
    for i, key in enumerate(MHDR_FIELDS):
        if key in ('flags', 'mcin', 'a13', 'a14', 'a15') or key is None:
            continue
        off = vals[i]
        if not off:
            chunks[key] = None
            continue
        pos = base + off
        size = struct.unpack_from('<I', data, pos + 4)[0]
        chunks[key] = bytearray(data[pos:pos + 8 + size])

    # Transform MMDX names.
    if chunks.get('mmdx') is not None and model_map:
        old_names = bytes(chunks['mmdx'][8:])
        names = _cstrs(chunks['mmdx'], 8, len(chunks['mmdx']))
        new = []
        for n in names:
            r = model_map(n)
            new.append(n if r is None else r)
        chunks['mmdx'] = _rebuild_cstr_chunk(CHUNK_MAGIC['mmdx'], new)
        if chunks.get('mmid') is None:
            raise ValueError('MMDX transform requires MMID')
        new_offsets = remap_name_table(old_names, chunks['mmdx'][8:],
                                       chunks['mmid'][8:])
        chunks['mmid'] = CHUNK_MAGIC['mmid'] + struct.pack('<I', len(new_offsets)) + new_offsets

    # Transform MCNKs (fixed-length area patch) and record their MCIN index.
    mcin_pos = base + vals[1]
    mcnk_slots = {}  # index(0..255) -> chunk bytes
    for i in range(256):
        off, sz, flags, asyncid = struct.unpack_from('<4I', data, mcin_pos + 8 + i * 16)
        if off and sz:
            b = bytearray(data[off:off + 8 + sz])
            area = struct.unpack_from('<I', b, 0x3C)[0]
            na = area_map(area) if area_map else area
            if na != area:
                struct.pack_into('<I', b, 0x3C, na)
            mcnk_slots[i] = bytes(b)

    # ---- Re-layout ----
    # Correct ADT order: MVER | MHDR(72) | MCIN(8+4096) | body chunks | MCNKs.
    # MCIN must sit at a fixed offset (84) so the extractor's hardcoded
    # `getMCNK = MCIN + offsMCNK - 84` resolves to absolute file offsets.
    body_chunks = [k for k in ['mtex', 'mmdx', 'mmid', 'mwmo', 'mwid',
                               'mddf', 'modf', 'mh2o', 'mfbo', 'mtxf', 'mtcg']
                   if chunks.get(k) is not None]

    base_new = len(mver) + 8  # offset base for MHDR (data start)
    out = bytearray()
    out += mver
    out += RDHM + struct.pack('<I', 64) + b'\x00' * 64  # placeholder MHDR

    # MCIN immediately after MHDR (offset 84 = 12 + 72).
    mcin_off_abs = len(out)
    out += NICM + struct.pack('<I', 4096) + b'\x00' * 4096  # placeholder

    def emit(chunk_bytes):
        out.extend(chunk_bytes)
        return len(out) - len(chunk_bytes)

    body_offsets = {}
    for k in body_chunks:
        body_offsets[k] = emit(chunks[k])

    mcnk_offsets = {}
    for i in sorted(mcnk_slots):
        mcnk_offsets[i] = len(out)
        out.extend(mcnk_slots[i])

    # Fill MHDR offsets (relative to base_new).
    new_vals = list(vals)
    new_vals[1] = mcin_off_abs - base_new  # mcin
    for k, abs_off in body_offsets.items():
        idx = MHDR_FIELDS.index(k)
        new_vals[idx] = abs_off - base_new
    # fill MHDR data
    struct.pack_into('<16I', out, len(mver) + 8, *new_vals)

    # Fill MCIN entries (absolute offsets + size).
    for i in range(256):
        if i in mcnk_offsets:
            abs_off = mcnk_offsets[i]
            sz = len(mcnk_slots[i]) - 8
            struct.pack_into('<4I', out, mcin_off_abs + 8 + i * 16,
                             abs_off, sz, 0, 0)
        else:
            struct.pack_into('<4I', out, mcin_off_abs + 8 + i * 16, 0, 0, 0, 0)

    return bytes(out)

def convert_file(src, dst, area_map=None, model_map=None):
    with open(src, 'rb') as f:
        data = f.read()
    out = convert_adt(data, area_map, model_map)
    with open(dst, 'wb') as f:
        f.write(out)
    return out
