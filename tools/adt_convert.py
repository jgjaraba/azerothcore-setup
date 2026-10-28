#!/usr/bin/env python3
"""Vanilla 1.12 -> WotLK 3.3.5 ADT converter (full re-serializer).

This retains terrain and legacy MCLQ water without translating liquid data.
The rewrite:
  1. remaps MMDX model names (e.g. `.mdx` -> `.m2`) via a model map,
  2. remaps MCNK area IDs via an area map,
and re-emits the file with recalculated MHDR offsets and MCIN entries.

Liquid policy: preserve MCNK flags, MCLQ offsets/size, masks, heights and bytes.
Do not manufacture MH2O or change alpha/liquid flags. ADT/v18 documents legacy
MCLQ client support (https://wowdev.wiki/ADT/v18#MCLQ_sub-chunk); AzerothCore's
map_extractor/adt.h and System.cpp also read it using MCNK.sizeMCLQ, not its
often-zero internal size. This is structural preservation, not a render test.
"""
import struct
from adt_refs import remap_name_table
from adt import CHUNK_MAGIC, MHDR_FIELDS, _adt_layout

REVM = b'REVM'
RDHM = b'RDHM'
NICM = b'NICM'

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
    _, vals, offsets, entries, ends = _adt_layout(data)
    mver = data[:12]

    # Extract body chunks (raw magic+size+data) via MHDR offsets.
    chunks = {}
    for key in MHDR_FIELDS[2:12]:
        pos = offsets[key]
        if not pos:
            chunks[key] = None
            continue
        chunks[key] = bytearray(data[pos:ends[pos]])

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
    mcnk_slots = {}  # index(0..255) -> chunk bytes
    for i, (off, sz, flags, asyncid) in enumerate(entries):
        if off and sz:
            b = bytearray(data[off:ends[off]])
            area = struct.unpack_from('<I', b, 0x3C)[0]
            na = area_map(area) if area_map else area
            if na != area:
                struct.pack_into('<I', b, 0x3C, na)
            mcnk_slots[i] = bytes(b)

    # ---- Re-layout ----
    # Correct ADT order: MVER | MHDR(72) | MCIN(8+4096) | body chunks | MCNKs.
    # MCIN must sit at a fixed offset (84) so the extractor's hardcoded
    # `getMCNK = MCIN + offsMCNK - 84` resolves to absolute file offsets.
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
    keys_by_pos = {pos: key for key, pos in offsets.items() if pos}
    for pos, end in ends.items():
        if pos in (0, 12, offsets['mcin']) or data[pos:pos + 4] == b'KNCM':
            continue
        k = keys_by_pos.get(pos)
        new_pos = emit(chunks[k] if k in chunks else data[pos:end])
        if k:
            body_offsets[k] = new_pos

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
            sz = len(mcnk_slots[i])
            struct.pack_into('<4I', out, mcin_off_abs + 8 + i * 16,
                             abs_off, sz, entries[i][2], entries[i][3])
        else:
            struct.pack_into('<4I', out, mcin_off_abs + 8 + i * 16,
                             0, 0, entries[i][2], entries[i][3])

    return bytes(out)

def convert_file(src, dst, area_map=None, model_map=None):
    with open(src, 'rb') as f:
        data = f.read()
    out = convert_adt(data, area_map, model_map)
    with open(dst, 'wb') as f:
        f.write(out)
    return out
