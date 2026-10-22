#!/usr/bin/env python3
"""Read-only ADT/WDT parsing for Vanilla 1.12 and WotLK 3.3.5 terrain.

Chunk magics are stored byte-reversed in the file (MVER -> "REVM", MHDR -> "RDHM",
MCIN -> "NICM", MTEX -> "XETM", MMDX -> "XDMM", MWMO -> "OMWM", MFBO -> "OBFM").
Offsets in MCIN point at absolute file positions of MCNK chunks.

The optional MHDR field labels are incomplete/incorrect for wet maps; this
is the dry-pilot reader, not a generic validator. See compatibility.md.
"""
import struct

REVM = b'REVM'
MCIN = b'NICM'
MTEX = b'XETM'
MMDX = b'XDMM'
MWMO = b'OMWM'
MFBO = b'OBFM'
MCNK = b'KNCM'

def _find(data, magic, start=0):
    return data.find(magic, start)

def _read_cstrs(data, off, end=None):
    out = []
    p = off
    limit = end if end is not None else len(data)
    while p < limit:
        e = data.find(b'\x00', p, limit)
        if e == -1 or e == p:
            break
        out.append(data[p:e].decode('latin1', errors='replace'))
        p = e + 1
    return out

def _mhdr_offsets(data):
    """Return dict of chunk data offsets using MHDR (offsets relative to MHDR
    data start = magic+8)."""
    mhdr = data.find(b'RDHM', 0, 0x100)
    if mhdr == -1:
        raise ValueError('no MHDR')
    base = mhdr + 8
    vals = struct.unpack_from('<16I', data, base)
    return {
        'mcin': base + vals[1] if vals[1] else 0,
        'mtex': base + vals[2] if vals[2] else 0,
        'mmdx': base + vals[3] if vals[3] else 0,
        'mmid': base + vals[4] if vals[4] else 0,
        'mwmo': base + vals[5] if vals[5] else 0,
        'mwid': base + vals[6] if vals[6] else 0,
        'mddf': base + vals[7] if vals[7] else 0,
        'modf': base + vals[8] if vals[8] else 0,
        'mh2o': base + vals[9] if vals[9] else 0,
    }

def _chunk_size(data, magic_pos):
    return struct.unpack_from('<I', data, magic_pos + 4)[0]

def parse_adt(path):
    with open(path, 'rb') as f:
        data = f.read()
    if data[:4] != REVM:
        raise ValueError('not an ADT (no REVM magic): %r' % data[:4])

    offs = _mhdr_offsets(data)

    mcin_off = offs['mcin']
    if not mcin_off:
        raise ValueError('no MCIN chunk')

    entries_off = mcin_off + 8
    entries = []
    for i in range(256):
        off, size, flags, asyncid = struct.unpack_from('<4I', data, entries_off + i * 16)
        entries.append((off, size))

    # MCNK chunk: magic(4) + size(4) + header(0x80). areaId at magic+0x3C.
    area_ids = []
    for off, size in entries:
        if off == 0 or size == 0 or off + 0x3C + 4 > len(data):
            area_ids.append(0)
            continue
        area_ids.append(struct.unpack_from('<I', data, off + 0x3C)[0])

    textures = []
    if offs['mtex']:
        textures = _read_cstrs(data, offs['mtex'] + 8, offs['mtex'] + 8 + _chunk_size(data, offs['mtex']))

    models = []
    if offs['mmdx']:
        models = _read_cstrs(data, offs['mmdx'] + 8, offs['mmdx'] + 8 + _chunk_size(data, offs['mmdx']))

    wmos = []
    if offs['mwmo']:
        wmos = _read_cstrs(data, offs['mwmo'] + 8, offs['mwmo'] + 8 + _chunk_size(data, offs['mwmo']))

    has_mfbo = data.find(MFBO, 0, len(data)) != -1

    return {
        'area_ids': area_ids,
        'textures': textures,
        'models': models,
        'wmos': wmos,
        'mfbo': has_mfbo,
    }

if __name__ == '__main__':
    import sys
    for p in sys.argv[1:]:
        r = parse_adt(p)
        areas = sorted(set(a for a in r['area_ids'] if a))
        print(p, 'areas=', areas, 'ntex=', len(r['textures']), 'nmdl=', len(r['models']), 'nwmo=', len(r['wmos']))
