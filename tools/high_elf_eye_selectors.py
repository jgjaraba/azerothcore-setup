"""Wrath facial channel17 selects 1700 + column7; Turtle eyes use 1702.

Transform data, never the frozen input MPQ or the source-preserved eye material.
"""
import struct


def require(ok, message):
    if not ok:
        raise ValueError(message)


def fix_selectors(raw, geometry):
    """Preserve every byte except the 22 race22 uint32 selectors (0 -> 2).

    Already-fixed tables are accepted; partial migrations and unknown values fail
    closed. Disk rows are eight uint32s, not the native in-memory 36-byte stride.
    """
    require(len(raw) >= 20 and raw[:4] == b'WDBC', 'Bad facial-style WDBC')
    count, fields, size, strings = struct.unpack_from('<4I', raw, 4)
    require((count, fields, size) == (270, 8, 32) and len(raw) == 20+count*size+strings,
            'Wrong facial-style row count/schema/length')
    rows = [struct.unpack_from('<8I', raw, 20+i*32) for i in range(count)]
    keys = [r[:3] for r in rows]
    require(len(set(keys)) == count, 'Duplicate facial-style natural keys')
    expected = {(22, sex, style) for sex in (0, 1) for style in range(11)}
    require({r[:3] for r in rows if r[0] == 22} == expected, 'Incomplete High Elf style coverage')
    require({r[7] for r in rows if r[0] == 22} in ({0}, {2}),
            'Unknown or partially migrated High Elf eye selectors')
    require(all(1702 in geometry.get((22, sex), set()) for sex in (0, 1)),
            'Missing High Elf eye geoset1702')
    result = bytearray(raw)
    for i, row in enumerate(rows):
        if row[0] == 22:
            struct.pack_into('<I', result, 20+i*32+28, 2)
    return bytes(result)


def eye_models(payload, sexes=('Male', 'Female')):
    """Validate actual converted M2/SKIN eye batches, retaining type8 and 17/4."""
    payload = {k.replace('\\', '/').lower(): v for k, v in payload.items()}
    geometry, report = {}, {}
    def array(raw, offset, width):
        require(len(raw) >= offset+8, 'Truncated eye model header')
        count, start = struct.unpack_from('<2I', raw, offset)
        require(start+count*width <= len(raw), 'Truncated eye model array')
        return [raw[start+i*width:start+(i+1)*width] for i in range(count)]
    for name in sexes:
        sex = ('Male', 'Female').index(name)
        base = f'character/custom/turtlehighelf/{name}/turtlehighelf{name}'.lower()
        require(base+'.m2' in payload and base+'00.skin' in payload, 'Missing High Elf M2/SKIN')
        model, skin = payload[base+'.m2'], payload[base+'00.skin']
        require(model[:8] == b'MD20\x08\x01\0\0' and skin[:4] == b'SKIN', 'Wrong eye model format')
        sections = array(skin, 28, 48)
        ids = [struct.unpack_from('<H', s)[0] for s in sections]
        require(ids.count(1702) == 1, 'Expected exactly one High Elf eye geoset1702')
        index = ids.index(1702)
        materials = array(model, 112, 4)
        textures = array(model, 80, 16)
        lookups = array(model, 128, 2)
        batches = [struct.unpack('<BBhHHhHHHHHHH', b) for b in array(skin, 36, 24)]
        eyes = [b for b in batches if b[3] == index]
        require(len(eyes) == 1, 'Expected exactly one High Elf eye batch')
        batch = eyes[0]
        require(batch[6] < len(materials) and materials[batch[6]] == struct.pack('<2H', 17, 4),
                'High Elf eyes must retain source unlit/additive material17/4')
        require(batch[9] < len(lookups), 'Invalid eye texture lookup')
        texture = struct.unpack('<H', lookups[batch[9]])[0]
        require(texture < len(textures) and struct.unpack_from('<I', textures[texture])[0] == 8,
                'High Elf eyes must retain replaceable TextureType8')
        geometry[(22, sex)] = set(ids)
        report[name] = {'geoset': 1702, 'section_index': index, 'material': [17, 4], 'texture_type': 8}
    return geometry, report
