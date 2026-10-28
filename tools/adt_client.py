"""Bounded MCNK framing for the 3.3.5a legacy-fix scanner (7C3A10).

Offsets include the outer chunk header. Never search opaque payloads for magic.
MCNR's 435 declared bytes have 13 physical padding bytes; legacy MCAL uses
sizeAlpha including its header. MCLQ uses sizeLiquid only when it exceeds 8.
"""
import struct


KNOWN = {b'TVCM', b'RNCM', b'YLCM', b'FRCM', b'HSCM', b'LACM',
         b'QLCM', b'ESCM', b'VCCM', b'VLCM'}
POINTERS = ((0x1C, b'TVCM'), (0x20, b'RNCM'), (0x24, b'YLCM'),
            (0x28, b'FRCM'), (0x2C, b'LACM'), (0x34, b'HSCM'),
            (0x60, b'ESCM'), (0x68, b'QLCM'), (0x7C, b'VCCM'))


def u32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def scan_mcnk(cell):
    """Return (tag, start, end) blocks; reject unknown tags/overruns/overlaps.

    This models the application's legacy-fix argument=1, with additional bounds
    checks. Active liquid extents must be anchored by the actual liquid pointer.
    Inactive MCLQ must already be self-length; its payload is never interpreted.
    """
    if len(cell) < 136 or cell[:4] != b'KNCM' or u32(cell, 4) != len(cell) - 8:
        raise ValueError('invalid MCNK framing')
    refs = {}
    for field, tag in POINTERS:
        p = u32(cell, field)
        if 136 <= p <= len(cell) - 8 and cell[p:p + 4] == tag:
            refs[p] = tag
    active = u32(cell, 0x6C) > 8
    if active and refs.get(u32(cell, 0x68)) != b'QLCM':
        raise ValueError('invalid active MCLQ offset')
    blocks, p = [], 136
    while p < len(cell):
        if p + 8 > len(cell):
            raise ValueError('truncated MCNK subchunk header')
        tag, size = bytes(cell[p:p + 4]), u32(cell, p + 4)
        if tag not in KNOWN:
            raise ValueError('unknown MCNK tag at %#x: %r' % (p, tag))
        if tag == b'RNCM':
            if size not in (435, 448):
                raise ValueError('unexpected MCNR size')
            size = 448
        elif tag == b'LACM':
            if u32(cell, 0x30) != size + 8:
                raise ValueError('legacy MCAL sizeAlpha must include header')
        elif tag == b'QLCM' and active:
            if p != u32(cell, 0x68):
                raise ValueError('MCLQ does not match active offset')
            size = u32(cell, 0x6C) - 8
        end = p + 8 + size
        if end > len(cell):
            raise ValueError('MCNK subchunk exceeds cell')
        if any(p < q < end for q in refs):
            raise ValueError('MCNK subchunk overlaps referenced subchunk')
        blocks.append((tag, p, end))
        p = end
    if any(not any(p == q and tag == expected for tag, p, _ in blocks)
           for q, expected in refs.items()):
        raise ValueError('MCNK reference is not a scanned boundary')
    return blocks


def self_length_mclq(cell):
    """Normalize only active MCLQ's own four-byte size before deactivation.

    Use the still-live (possibly relocated) offset/size, never a magic search or
    a guessed payload extent. Native inactive self-length blocks are unchanged.
    """
    blocks = scan_mcnk(cell)
    if u32(cell, 0x6C) <= 8:
        return cell
    p, size = u32(cell, 0x68), u32(cell, 0x6C) - 8
    if not any(tag == b'QLCM' and start == p and end == p + size + 8
               for tag, start, end in blocks):
        raise ValueError('active MCLQ extent not verified')
    out = bytearray(cell)
    struct.pack_into('<I', out, p + 4, size)
    return bytes(out)
