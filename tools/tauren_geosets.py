"""Append the four missing Tauren facial geosets to native Wrath assets.

Keeps native skeleton/animation/material data and every old vertex/skin record.
Copies only missing weighted sections from the classic model, after checking
every referenced bone and parent has the same identity and bind pivot. This is
an asset conversion, not a whole-model replacement from Vanilla.
"""
import struct
import numpy as np


def require(ok, message):
    if not ok:
        raise ValueError(message)


def array(raw, header, width):
    n, offset = struct.unpack_from('<2I', raw, header)
    require(offset + n * width <= len(raw), 'Array outside model/skin')
    return [raw[offset + width*i:offset + width*(i+1)] for i in range(n)]


def ushorts(records):
    return [struct.unpack('<H', record)[0] for record in records]


def append(raw, header, rows):
    while len(raw) % 16:
        raw.append(0)
    offset = len(raw)
    raw.extend(b''.join(rows))
    struct.pack_into('<2I', raw, header, len(rows), offset)


def convert(source, native, skins, sex):
    require(source[:8] == b'MD20' + struct.pack('<I', 256), 'Expected classic M2')
    require(native[:8] == b'MD20' + struct.pack('<I', 264), 'Expected Wrath M2')
    expected = {110, 111} if sex == 0 else {206, 207}
    source_bones, native_bones = array(source, 52, 108), array(native, 44, 88)
    require(len(source_bones) == len(native_bones), 'Different skeleton sizes')
    source_vertices, native_vertices = array(source, 68, 48), array(native, 60, 48)
    nviews, views = struct.unpack_from('<2I', source, 76)
    require(nviews == 1 and len(skins) == struct.unpack_from('<I', native, 68)[0], 'Unexpected LOD count')
    source_lookup = ushorts(array(source, views, 2))
    source_triangles = ushorts(array(source, views + 8, 2))
    source_sections = array(source, views + 24, 32)
    source_batches = array(source, views + 32, 24)
    source_textures = array(source, 92, 16)
    source_texlookup = ushorts(array(source, 148, 2))
    source_flags = array(source, 132, 4)
    native_textures = array(native, 80, 16)
    native_texlookup = ushorts(array(native, 128, 2))
    flags = array(native, 112, 4)
    bonelookup = array(native, 120, 2)
    additions, checked = [], set()

    def verify_bone(index):
        if index in checked:
            return
        require(0 <= index < len(source_bones), 'Vertex bone outside skeleton')
        a, b = source_bones[index], native_bones[index]
        require(a[:12] == b[:12] and a[-12:] == b[-12:], f'Bind skeleton mismatch on used bone {index}')
        checked.add(index)
        parent, = struct.unpack_from('<h', a, 8)
        if parent >= 0:
            verify_bone(parent)

    for si, section in enumerate(source_sections):
        fields = struct.unpack('<10H3f', section)
        if fields[0] not in expected:
            continue
        require(fields[1] == 0, 'Unsupported high triangle level')
        start, count, first, nindices = fields[2:6]
        local_globals = source_lookup[start:start + count]
        triangles = source_triangles[first:first + nindices]
        require(len(local_globals) == count and len(triangles) == nindices and nindices % 3 == 0,
                'Truncated source section')
        require(all(start <= index < start + count for index in triangles), 'Triangle outside section')
        vertices = [source_vertices[index] for index in local_globals]
        used = sorted({bone for vertex in vertices for weight, bone in zip(vertex[12:16], vertex[16:20]) if weight})
        for bone in used:
            verify_bone(bone)
        combo = len(bonelookup)
        bonelookup += [struct.pack('<H', bone) for bone in used]
        base = len(native_vertices)
        native_vertices += vertices
        batches = [row for row in source_batches if struct.unpack_from('<H', row, 4)[0] == si]
        require(len(batches) == 1, 'Expected one source material per extra section')
        batch = batches[0]
        material = source_flags[struct.unpack_from('<H', batch, 10)[0]]
        if material not in flags:
            flags.append(material)
        texture_index = source_texlookup[struct.unpack_from('<H', batch, 16)[0]]
        texture_type, = struct.unpack_from('<I', source_textures[texture_index])
        require(texture_type == 8, 'Extra facial sections must use native extra-skin texture')
        additions.append(dict(id=fields[0], vertices=vertices, global_start=base,
                              triangles=[i-start for i in triangles], combo=combo, used=used,
                              material=flags.index(material), source_section=si))
    require({a['id'] for a in additions} == expected and len(additions) == (2 if sex == 0 else 3),
            'Missing expected extra facial meshes')
    require(len(native_vertices) < 65536 and len(bonelookup) < 65536, '16-bit model capacity exceeded')
    result = bytearray(native)
    append(result, 60, native_vertices)
    append(result, 112, flags)
    append(result, 120, bonelookup)
    # Existing geometry, skeleton, animations and all other original bytes stay.
    allowed = set(range(60, 68)) | set(range(112, 128))
    require(all(result[i] == value for i, value in enumerate(native) if i not in allowed),
            'Unexpected native M2 prefix mutation')
    output_skins = []
    for native_skin in skins:
        require(native_skin[:4] == b'SKIN', 'Expected Wrath skin')
        lookup = array(native_skin, 4, 2)
        triangles = array(native_skin, 12, 2)
        properties = array(native_skin, 20, 4)
        sections = array(native_skin, 28, 48)
        batches = array(native_skin, 36, 24)
        require(len(lookup) == len(properties), 'Native bone properties/vertex lookup count mismatch')
        require(not expected.intersection(struct.unpack_from('<H', s)[0] for s in sections),
                'Extra geoset already exists')
        templates = [r for r in batches if struct.unpack_from('<H', r, 14)[0] == 1 and
                     struct.unpack_from('<I', native_textures[native_texlookup[struct.unpack_from('<H', r, 16)[0]]])[0] == 8]
        require(templates, 'No compatible native extra-skin batch')
        for extra in additions:
            require(len(extra['used']) <= struct.unpack_from('<I', native_skin, 44)[0],
                    'LOD bone palette capacity exceeded')
            vs, ts = len(lookup), len(triangles)
            lookup += [struct.pack('<H', extra['global_start'] + i) for i in range(len(extra['vertices']))]
            triangles += [struct.pack('<H', vs + i) for i in extra['triangles']]
            local = {bone: i for i, bone in enumerate(extra['used'])}
            properties += [bytes(local[bone] if weight else 0 for weight, bone in zip(v[12:16], v[16:20]))
                           for v in extra['vertices']]
            positions = np.array([struct.unpack_from('<3f', v) for v in extra['vertices']])
            center, box = positions.mean(0), (positions.min(0) + positions.max(0))/2
            radius = float(np.linalg.norm(positions-box, axis=1).max())
            old_bounds = np.array(struct.unpack_from('<6f', native, 160)).reshape(2, 3)
            require(np.all(positions >= old_bounds[0]-1e-4) and np.all(positions <= old_bounds[1]+1e-4),
                    'New mesh exceeds native visibility bounds')
            influences = max(sum(w > 0 for w in v[12:16]) for v in extra['vertices'])
            sections.append(struct.pack('<10H7f', extra['id'], 0, vs, len(extra['vertices']), ts,
                                         len(extra['triangles']), len(extra['used']), extra['combo'],
                                         influences, 0, *center, *box, radius))
            batch = bytearray(templates[0])
            struct.pack_into('<HH', batch, 4, len(sections)-1, len(sections)-1)
            struct.pack_into('<H', batch, 10, extra['material'])
            batches.append(bytes(batch))
        require(len(lookup) < 65536 and len(triangles) < 65536, '16-bit skin capacity exceeded')
        output = bytearray(native_skin)
        for header, rows in ((4, lookup), (12, triangles), (20, properties), (28, sections), (36, batches)):
            append(output, header, rows)
        output_skins.append(bytes(output))
    return bytes(result), output_skins, dict(geosets=sorted(expected), sections=len(additions),
        added_vertices=sum(len(a['vertices']) for a in additions), skeleton_bones_verified=sorted(checked),
        preserved_native_animation_bytes=True, native_prefix_only_array_headers_changed=True)
