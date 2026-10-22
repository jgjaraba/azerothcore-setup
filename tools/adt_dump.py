#!/usr/bin/env python3
"""Dump the chunk tree of an ADT/WDT for format comparison (Phase II).

Chunk magics are stored reversed. Known reversed magics:
  REVM(MVER) RDHM(MHDR) NICM(MCIN) XETM(MTEX) XDMM(MMDX) DIMM(MMID)
  OMWM(MWMO) DIWM(MWID) FDDM(MDDF) FDOM(MODF) O2HM(MH2O) OBFM(MFBO)
  FXTM(MTXF) GCTM(MTCG) KNCM(MCNK) TVCM(MCVT) RNCM(MCNR) YLCM(MCLY)
  FRCM(MCRF) LACM(MCAL) HSCM(MCSH) VLCM(MCLV) VCCM(MCCV)
"""
import struct, sys

MAGICS = {
    b'REVM': 'MVER', b'RDHM': 'MHDR', b'NICM': 'MCIN', b'XETM': 'MTEX',
    b'XDMM': 'MMDX', b'DIMM': 'MMID', b'OMWM': 'MWMO', b'DIWM': 'MWID',
    b'FDDM': 'MDDF', b'FDOM': 'MODF', b'O2HM': 'MH2O', b'OBFM': 'MFBO',
    b'FXTM': 'MTXF', b'GCTM': 'MTCG', b'KNCM': 'MCNK', b'TVCM': 'MCVT',
    b'RNCM': 'MCNR', b'YLCM': 'MCLY', b'FRCM': 'MCRF', b'LACM': 'MCAL',
    b'HSCM': 'MCSH', b'VLCM': 'MCLV', b'VCCM': 'MCCV', b'LMCM': 'MCSE',
}

def scan_chunks(data, start, end, depth=0):
    p = start
    while p + 8 <= end:
        magic = data[p:p+4]
        name = MAGICS.get(magic)
        size = struct.unpack_from('<I', data, p+4)[0]
        if name is None:
            return
        yield p, name, size
        p += 8 + size

def dump_adt(path, max_mcnk=3):
    with open(path, 'rb') as f:
        data = f.read()
    print(f'## {path} ({len(data)} bytes)')
    # top-level chunks up to first MCNK
    mcnk_positions = []
    for p, name, size in scan_chunks(data, 0, len(data)):
        if name == 'MCIN':
            # read 256 entries
            base = p + 8
            for i in range(256):
                off, sz, flags, asyncid = struct.unpack_from('<4I', data, base + i*16)
                if off and sz:
                    mcnk_positions.append(off)
            print(f'  MCIN @ {p:#x} -> {len([x for x in mcnk_positions if x])} non-empty MCNK')
            continue
        if name == 'MCNK':
            continue
        print(f'  {name} @ {p:#x} size={size}')
        if name == 'MTEX':
            # print texture count
            q = p + 8
            n = 0
            while q < p + 8 + size:
                e = data.find(b'\x00', q, p + 8 + size)
                if e == -1 or e == q:
                    break
                n += 1
                q = e + 1
            print(f'      (textures: {n})')
        if name == 'MH2O':
            print(f'      (MH2O present)')
    # dump first few MCNK sub-chunks
    for i, off in enumerate(mcnk_positions[:max_mcnk]):
        print(f'  MCNK[{i}] @ {off:#x}:')
        # MCNK header is 0x80 bytes; sub-chunks follow
        area = struct.unpack_from('<I', data, off + 0x34)[0]
        nlayers = struct.unpack_from('<I', data, off + 0x0C)[0]
        holes = struct.unpack_from('<I', data, off + 0x3C)[0]
        print(f'      areaId={area} nLayers={nlayers} holes={holes:#x}')
        for sp, sname, ssize in scan_chunks(data, off + 0x80, off + 0x80 + 0x4000):
            extra = ''
            if sname == 'MCLY':
                cnt = ssize // 16
                # layer flags are at offset 0x08 of each 16-byte entry
                flags = [struct.unpack_from('<I', data, sp + 8 + j*16)[0] for j in range(cnt)]
                extra = f' ({cnt} layers, flags={[hex(x) for x in flags]})'
            print(f'      {sname} @ {sp:#x} size={ssize}{extra}')

if __name__ == '__main__':
    for p in sys.argv[1:]:
        dump_adt(p)
