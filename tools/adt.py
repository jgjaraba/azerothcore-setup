#!/usr/bin/env python3
"""Read-only ADT/WDT parsing for Vanilla 1.12 and WotLK 3.3.5 terrain.

Chunk magics are stored byte-reversed in the file (MVER -> "REVM", MHDR -> "RDHM",
MCIN -> "NICM", MTEX -> "XETM", MMDX -> "XDMM", MWMO -> "OMWM", MFBO -> "OBFM").
Offsets in MCIN point at absolute file positions of MCNK chunks.

Framing and referenced chunks are validated before reading payloads. Liquid
payloads remain opaque; this is not a semantic liquid/alpha validator.
"""
import struct

REVM = b'REVM'
MCIN = b'NICM'
MTEX = b'XETM'
MMDX = b'XDMM'
MWMO = b'OMWM'
MFBO = b'OBFM'
MCNK = b'KNCM'

# WotLK MHDR: fields 12..15 are reserved, NOT chunk offsets.
MHDR_FIELDS = ['flags', 'mcin', 'mtex', 'mmdx', 'mmid', 'mwmo', 'mwid',
               'mddf', 'modf', 'mfbo', 'mh2o', 'mtxf',
               'reserved12', 'reserved13', 'reserved14', 'reserved15']
CHUNK_MAGIC = {key: key.upper()[::-1].encode('ascii')
               for key in MHDR_FIELDS[1:12]}


def _chunk_end(data, pos, magic=None, limit=None):
    limit = len(data) if limit is None else limit
    if pos < 0 or pos + 8 > limit:
        raise ValueError('chunk header out of bounds at %d' % pos)
    if magic is not None and data[pos:pos + 4] != magic:
        raise ValueError('wrong chunk magic at %d: expected %r' % (pos, magic))
    end = pos + 8 + struct.unpack_from('<I', data, pos + 4)[0]
    if end > limit:
        raise ValueError('chunk payload out of bounds at %d' % pos)
    return end


def _adt_layout(data):
    """Validate framing; return MHDR base/values, offsets, MCIN, chunk ends.

    MCIN normally includes the MCNK's eight-byte header. Also accept payload
    sizes written by the original pilot serializer; never use MCIN to slice.
    """
    if _chunk_end(data, 0, REVM) != 12 or struct.unpack_from('<I', data, 8)[0] != 18:
        raise ValueError('expected MVER 18')
    if _chunk_end(data, 12, b'RDHM') != 84:
        raise ValueError('expected 64-byte MHDR')
    base = 20
    vals = struct.unpack_from('<16I', data, base)
    ends = {}
    pos = 0
    while pos < len(data):
        end = _chunk_end(data, pos)
        ends[pos] = end
        pos = end
    for magic in (REVM, b'RDHM', MCIN):
        if sum(data[p:p + 4] == magic for p in ends) != 1:
            raise ValueError('missing or duplicate %r' % magic)
    offs = {}
    for i, key in enumerate(MHDR_FIELDS[1:12], 1):
        pos = base + vals[i] if vals[i] else 0
        offs[key] = pos
        if pos:
            if pos not in ends:
                raise ValueError('MHDR %s is not a chunk boundary' % key)
            _chunk_end(data, pos, CHUNK_MAGIC[key])
    mcin = offs['mcin']
    if not mcin or ends[mcin] - mcin != 4104:
        raise ValueError('expected 4096-byte MCIN')
    entries = []
    seen = set()
    for i in range(256):
        off, size, flags, asyncid = struct.unpack_from('<4I', data, mcin + 8 + i * 16)
        entries.append((off, size, flags, asyncid))
        if not off and not size:
            continue
        if not off or not size or off not in ends or off in seen:
            raise ValueError('invalid or duplicate MCIN slot %d' % i)
        end = _chunk_end(data, off, MCNK)
        if end - off < 136 or size not in (end - off, end - off - 8):
            raise ValueError('MCIN/MCNK size mismatch in slot %d' % i)
        seen.add(off)
        # MCLQ's own size is commonly zero in Vanilla. The MCNK header
        # supplies the extent including the MCLQ header (even for dry cells).
        liquid, liquid_size = struct.unpack_from('<2I', data, off + 0x68)
        # Only active liquids are dereferenced by the client. Real dry Turtle
        # cells also use size=8 with offset=0 or UINT32_MAX; retain those bytes.
        if liquid_size > 8 and liquid:
            lp = off + liquid
            if liquid < 136 or lp + 8 > end or data[lp:lp + 4] != b'QLCM':
                raise ValueError('invalid MCLQ offset/magic in slot %d' % i)
            if lp + liquid_size > end:
                raise ValueError('MCLQ out of MCNK bounds in slot %d' % i)
        elif liquid_size > 8:
            raise ValueError('MCLQ size without offset in slot %d' % i)
    if seen != {p for p in ends if data[p:p + 4] == MCNK}:
        raise ValueError('unindexed MCNK chunk')
    return base, vals, offs, entries, ends

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
    """Return absolute chunk-header positions resolved from MHDR offsets."""
    return _adt_layout(data)[2]

def _chunk_size(data, magic_pos):
    return struct.unpack_from('<I', data, magic_pos + 4)[0]

def parse_adt(path):
    with open(path, 'rb') as f:
        data = f.read()
    if data[:4] != REVM:
        raise ValueError('not an ADT (no REVM magic): %r' % data[:4])

    _, _, offs, entries, _ = _adt_layout(data)

    # MCNK chunk: magic(4) + size(4) + header(0x80). areaId at magic+0x3C.
    area_ids = []
    for off, size, flags, asyncid in entries:
        if off == 0:
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

    has_mfbo = bool(offs['mfbo'])

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
