#!/usr/bin/env python3
"""Close the 24 high-elf ADTs against read-only client snapshots.

Only writes a fresh staging directory: files/, evidence/, manifest.json. No MPQ,
DBC, installation or converter modification. Native resources remain external
requirements, with exact archive/member/content provenance. Missing resources
remain unresolved (never mapped to a similar-looking model or texture).
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess

from adt import CHUNK_MAGIC, MHDR_FIELDS
from adt_refs import name_offsets, remap_name_table
from high_elf_terrain import Tile, chunk, u32

ROOT = Path(__file__).resolve().parents[1]
NS = 'Character\\Custom\\HighElfMap'
WMO_LIQUID_MANIFEST = ROOT / 'tools/high-elf-wmo-liquids.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def client_path(value):
    value = value.replace('/', '\\')
    if (not value or any(p in ('', '.', '..') for p in value.split('\\'))
            or not re.fullmatch(r'[A-Za-z0-9_ .\\&()\-]+', value)):
        raise ValueError('Unsafe client path: ' + repr(value))
    return value


def key(value):
    return client_path(value).lower()


def model_path(value):
    value = client_path(value)
    return value[:-4] + '.m2' if value.lower().endswith(('.mdx', '.mdl')) else value


def isolated(value):
    value = model_path(value)
    stem, ext = value.rsplit('\\', 1)[-1].rsplit('.', 1)
    # Path identity, not just basename or bytes: VMap flattens filenames.
    return NS + '\\he_' + digest(key(value).encode())[:20] + '_' + stem.lower() + '.' + ext.lower()


def run(args):
    return subprocess.run([str(a) for a in args], capture_output=True, text=True)


# Compiled only into the candidate's evidence directory. Keeping archives open
# makes exhaustive direct-name probing practical, including unlisted members.
READER_CPP = r'''
#include <StormLib.h>
#include <cstdio>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>
int main(int argc, char** argv) {
    std::vector<HANDLE> archives;
    for (int i=1; i<argc; ++i) {
        HANDLE h=nullptr;
        if (!SFileOpenArchive(argv[i], 0, MPQ_OPEN_READ_ONLY, &h)) return 2;
        archives.push_back(h);
    }
    std::string name;
    while (std::getline(std::cin, name)) {
        uint32_t header[3]={0,0,0};
        std::vector<char> bytes;
        for (uint32_t i=0; i<archives.size(); ++i) {
            HANDLE f=nullptr;
            if (!SFileOpenFileEx(archives[i], name.c_str(), SFILE_OPEN_FROM_MPQ, &f)) {
                auto error=SErrGetLastError();
                if (error != ERROR_FILE_NOT_FOUND) {
                    header[0]=2; header[1]=i; header[2]=error; break;
                }
                continue;
            }
            DWORD high=0, n=SFileGetFileSize(f, &high), got=0;
            if (high || n==0xffffffff || n>512*1024*1024) {
                SFileCloseFile(f); header[0]=2; header[1]=i; break;
            }
            bytes.resize(n);
            bool ok = n && SFileReadFile(f, bytes.data(), n, &got, nullptr) && got==n;
            SFileCloseFile(f);
            header[0]=ok ? 1 : 2; header[1]=i; header[2]=ok ? n : 0;
            break;
        }
        if (fwrite(header, sizeof(header), 1, stdout)!=1) return 3;
        if (header[0]==1 && fwrite(bytes.data(), 1, bytes.size(), stdout)!=bytes.size()) return 3;
        fflush(stdout);
    }
    for (auto h: archives) SFileCloseArchive(h);
}
'''


def build_reader(evidence):
    source, binary = evidence / 'mpq-reader.cpp', evidence / 'mpq-reader'
    source.write_text(READER_CPP)
    result = run(['g++', '-O2', '-std=c++17', '-I', ROOT / 'tools/stormlib/include',
                  source, ROOT / 'tools/stormlib/lib/libstorm.a',
                  '-lz', '-lbz2', '-lpthread', '-ldl', '-o', binary])
    (evidence / 'mpq-reader-build.log').write_text(result.stdout + result.stderr)
    if result.returncode:
        raise ValueError('Cannot build read-only MPQ reader: ' + result.stderr)
    return binary


class Snapshot:
    """Explicit archive order, fresh listings, direct probes even without a listfile.

    Locale is explicit; other locales and old backup archives are not effective
    overrides. Root custom patches sort after numeric patches; locale patches
    have priority over root ones. This is an offline snapshot policy, not a claim
    about an arbitrary playing client's loader.
    """
    def __init__(self, root, kind, evidence, mpq, locale='esES', reader=None):
        self.root, self.kind, self.mpq = Path(root), kind, mpq
        self.evidence = evidence / kind
        self.evidence.mkdir(parents=True)
        self.cache, self.index, self.used, self.archive_hashes = {}, {}, set(), {}
        data = self.root / 'Data'
        all_arcs = [p for p in data.rglob('*') if p.suffix.lower() == '.mpq']
        base_order = (['wmo', 'texture', 'terrain', 'speech', 'sound', 'model',
                       'misc', 'interface', 'fonts', 'dbc', 'base', 'backup']
                      if kind == 'turtle' else
                      ['common', 'common-2', 'expansion', 'lichking'] +
                      [prefix + '-' + locale.lower() for prefix in
                       ('backup', 'base', 'speech', 'locale', 'expansion-locale',
                        'expansion-speech', 'lichking-locale', 'lichking-speech')])

        def priority(p):
            stem = p.stem.lower()
            if stem in base_order:
                return (0, base_order.index(stem), 0)
            match = re.fullmatch(r'patch(?:-' + re.escape(locale.lower()) + r')?(?:-([0-9a-z]+))?', stem)
            if match:
                suffix = match[1] or '0'
                return (1, int(suffix) if suffix.isdigit() else 1000 + ord(suffix[0]),
                        int(p.parent != data))
            raise ValueError('Unclassified archive: ' + str(p))

        self.archives = sorted([p for p in all_arcs if p.parent == data or
                                p.parent.name.lower() == locale.lower()],
                               key=lambda p: (priority(p), str(p)), reverse=True)
        for i, archive in enumerate(self.archives):
            result = run([mpq, 'list', archive])
            if result.returncode:
                raise ValueError('Cannot inventory ' + str(archive) + ': ' + result.stderr)
            (self.evidence / f'archive-{i:02}.txt').write_text(result.stdout)
            for line in result.stdout.splitlines():
                if '\t' not in line:
                    continue
                name, size = line.rsplit('\t', 1)
                try:
                    normalized = key(name)
                except ValueError:
                    continue  # MPQ internal/unnamed entries are not resource paths.
                self.index.setdefault(normalized, []).append((archive, name, int(size)))
        self.reader = subprocess.Popen([str(reader), *map(str, self.archives)],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE) if reader else None

    def close(self):
        if self.reader:
            self.reader.stdin.close()
            self.reader.stdout.close()
            if self.reader.wait() != 0:
                raise ValueError('Persistent MPQ reader failed')

    def get(self, name):
        name = client_path(name)
        normalized = key(name)
        if normalized in self.cache:
            return self.cache[normalized]
        # Probe every higher priority archive too: an incomplete listing is not
        # proof of absence, nor permission to fall through to a lower payload.
        destination = self.evidence / (digest(normalized.encode()) + '.bin')
        found = None
        if self.reader:
            self.reader.stdin.write(name.encode('ascii') + b'\n')
            self.reader.stdin.flush()
            header = self.reader.stdout.read(12)
            if len(header) != 12:
                raise ValueError('Persistent MPQ reader stopped')
            status, index, size = struct.unpack('<3I', header)
            if status == 2:
                raise ValueError(f'MPQ read/empty/deleted resource: {name} in {self.archives[index]} (error {size})')
            if status == 1:
                data = self.reader.stdout.read(size)
                if len(data) != size:
                    raise ValueError('Short MPQ read: ' + name)
                destination.write_bytes(data)
                archive = self.archives[index]
                self.used.add(archive)
                found = (data, {'snapshot': str(self.root), 'archive': str(archive),
                                'member': name, 'sha256': digest(data), 'bytes': len(data)})
            elif status != 0:
                raise ValueError('Invalid MPQ reader response')
            self.cache[normalized] = found
            return found
        for archive in self.archives:
            result = run([self.mpq, 'extract-one', archive, name, destination])
            if result.returncode:
                if 'not found' not in result.stderr.lower() and 'open file failed' not in result.stderr.lower():
                    raise ValueError('MPQ read failed: ' + str(archive) + ': ' + result.stderr)
                continue
            data = destination.read_bytes()
            if not data:
                raise ValueError('Effective empty/deleted resource: ' + name + ' in ' + str(archive))
            self.used.add(archive)
            found = (data, {'snapshot': str(self.root), 'archive': str(archive),
                            'member': name, 'sha256': digest(data), 'bytes': len(data)})
            break
        self.cache[normalized] = found
        return found

    def provenance(self):
        return [{'path': str(p), 'sha256': file_hash(p), 'bytes': p.stat().st_size}
                for p in self.archives]


def wmo_chunks(data):
    result, p = [], 0
    while p < len(data):
        if p + 8 > len(data):
            raise ValueError('Truncated WMO chunk header')
        n = u32(data, p + 4)
        if p + 8 + n > len(data):
            raise ValueError('Truncated WMO chunk payload')
        result.append((data[p:p + 4][::-1].decode('ascii'), data[p + 8:p + 8 + n]))
        p += 8 + n
    if not result or result[0] != ('MVER', struct.pack('<I', 17)):
        raise ValueError('Only WMO version 17 is supported')
    if len(dict(result)) != len(result):
        raise ValueError('Duplicate WMO root chunks')
    return result


def strings(data):
    """WMO strings may contain empty alignment padding; retain real starts."""
    result, pos = {}, 0
    while pos < len(data):
        end = data.find(b'\0', pos)
        if end < 0:
            raise ValueError('Unterminated string table')
        if end > pos:
            result[pos] = data[pos:end].decode('latin1')
        pos = end + 1
    return result


def wmo_liquid_audit(data, groups):
    """Structural 335 liquid interpretation, not a client/runtime simulation.

    With MOHD 0x4, legacy type 15 maps to 19 (WMO magma), even without
    a liquid grid. Without it, 15 is the no-liquid sentinel.
    """
    header = dict(wmo_chunks(data)).get('MOHD', b'')
    if len(header) != 64:
        raise ValueError('Invalid WMO MOHD for liquid audit')
    flags = struct.unpack_from('<H', header, 60)[0]
    records = []
    for name, raw in groups:
        bodies = dict(wmo_chunks(raw))
        mogp = bodies.get('MOGP', b'')
        if len(mogp) < 68:
            raise ValueError('Invalid WMO MOGP for liquid audit: ' + name)
        # The chunk walker also checks framing of every nested subchunk. It
        # cannot reuse wmo_chunks(), which requires an outer MVER.
        nested, pos = [], 68
        while pos < len(mogp):
            if pos + 8 > len(mogp) or pos + 8 + u32(mogp, pos + 4) > len(mogp):
                raise ValueError('Truncated WMO MOGP subchunk: ' + name)
            nested.append(mogp[pos:pos + 4][::-1].decode('ascii'))
            pos += 8 + u32(mogp, pos + 4)
        typ, group_flags = u32(mogp, 52), u32(mogp, 8)
        grid = 'MLIQ' in nested or 'MLIQ' in bodies
        sentinel = typ == 15 and not flags & 4
        records.append({'source': name, 'liquid_type': typ,
                        'group_flags': group_flags, 'has_MLIQ': grid,
                        'dry_sentinel': sentinel,
                        'legacy_15_to_19_bbox_magma': typ == 15 and bool(flags & 4)})
    return {'root_flags': flags, 'groups': records,
            'all_dry': bool(records) and all(r['dry_sentinel'] and
                        not r['has_MLIQ'] and not r['group_flags'] & 0x1000 for r in records)}


def adapt_wmo_dry_liquids(data, source, groups, policy):
    """Only explicitly hash/identity-locked source families may be adapted."""
    before = wmo_liquid_audit(data, groups)
    if key(source) != key(policy['source']) or digest(data) != policy['sha256']:
        raise ValueError('WMO dry-liquid root identity/hash guard: ' + source)
    if before['root_flags'] != policy['root_flags'] or not before['root_flags'] & 4:
        raise ValueError('WMO dry-liquid root flags guard: ' + source)
    if len(groups) != len(policy['groups']) or not groups:
        raise ValueError('WMO dry-liquid group count guard: ' + source)
    for (name, raw), expected, audit in zip(groups, policy['groups'], before['groups']):
        if (audit['liquid_type'] != 15 or audit['has_MLIQ'] or
                audit['group_flags'] & 0x1000):
            raise ValueError('WMO dry-liquid refuses non-sentinel/wet group: ' + name)
        if key(name) != key(expected['source']) or digest(raw) != expected['sha256']:
            raise ValueError('WMO dry-liquid group identity/hash guard: ' + name)
    # Patch the 16-bit MOHD flags in place; preserve all other root bytes.
    out, pos = bytearray(data), 0
    while out[pos:pos + 4] != b'DHOM':
        pos += 8 + u32(out, pos + 4)
    struct.pack_into('<H', out, pos + 8 + 60, before['root_flags'] & ~4)
    out = bytes(out)
    after = wmo_liquid_audit(out, groups)
    if not after['all_dry']:
        raise ValueError('WMO dry-liquid postcondition failed: ' + source)
    return out, {'before': before, 'after': after,
                 'source_sha256': digest(data), 'adapted_source_sha256': digest(out),
                 'field': 'MOHD.flags uint16 @60', 'operation': 'flags & ~0x4'}


def rewrite_wmo(data, resolve, adaptations=None):
    """Rebuild MOTX/MODN and all MOMT/MODD offsets, preserving opaque bytes."""
    ordered = wmo_chunks(data)
    bodies = dict(ordered)
    if len(bodies.get('MOHD', b'')) != 64:
        raise ValueError('Invalid WMO MOHD')
    dependencies = []
    for names, records, stride, fields in (
            ('MOTX', 'MOMT', 64, (12, 24, 36)), ('MODN', 'MODD', 40, (0,))):
        old = strings(bodies.get(names, b''))
        original_names = bodies.get(names, b'')
        out, offsets = bytearray(b'\0' * 4), {}
        for offset, name in old.items():
            target = resolve(name, 'm2' if names == 'MODN' else 'texture')
            if names == 'MODN' and target.lower().endswith('.m2'):
                # WMO's client contract uses MDX names even for Wrath M2 files.
                target = target[:-3] + '.mdx'
            dependencies.append({'kind': names, 'source': name, 'target': target})
            offsets[offset] = len(out)
            out.extend(target.encode('latin1') + b'\0')
            if names == 'MODN':
                out.extend(bytes((-len(out)) % 4))
        if names in bodies:
            bodies[names] = bytes(out)
        body = bytearray(bodies.get(records, b''))
        if len(body) % stride:
            raise ValueError('Misaligned WMO ' + records)
        for p in range(0, len(body), stride):
            if records == 'MOMT' and u32(body, p + 4) > 6:
                raise ValueError('WMO material shader not supported by Wrath: ' + str(u32(body, p + 4)))
            for field in fields:
                raw = u32(body, p + field)
                offset = raw & 0xffffff if records == 'MODD' else raw
                if offset not in offsets:
                    # MOTX contains zero padding used as explicit empty texture
                    # strings. Preserve that sentinel, including nonzero offsets.
                    if records == 'MOMT' and offset < len(original_names) and original_names[offset] == 0:
                        new = 0
                    elif (records == 'MOMT' and
                          (field == 36 or field == 24 and u32(body, p + 4) not in (3, 5, 6))):
                        # Legacy exporters stored scalar data in the third
                        # texture field (e.g. float 0.1). Wrath shaders 0..6
                        # never sample texture3; only 3/5/6 sample texture2.
                        # Rebase the inactive pointer to an empty MOTX sentinel,
                        # never to an unrelated texture or an out-of-file offset.
                        new = 0
                        if adaptations is not None:
                            adaptations.append({'material': p // 64, 'field': field, 'source_u32': raw,
                                                'target_empty_MOTX_offset': 0,
                                                'reason': 'Inactive texture slot for Wrath shader ' + str(u32(body, p + 4))})
                    else:
                        raise ValueError(f'{records} points outside {names}: {offset}')
                else:
                    new = offsets[offset]
                if records == 'MODD':
                    if new > 0xffffff:
                        raise ValueError('MODN exceeds 24-bit offset')
                    new |= raw & 0xff000000
                struct.pack_into('<I', body, p + field, new)
        if records in bodies:
            bodies[records] = bytes(body)
    return b''.join(chunk(n.encode()[::-1], bodies[n]) for n, _ in ordered), dependencies


def m2_textures(data):
    if len(data) < 304 or data[:4] != b'MD20' or u32(data, 4) not in (256, 264):
        raise ValueError('Unsupported M2 header (requires MD20 256/264)')
    field = 92 if u32(data, 4) == 256 else 80
    count, start = struct.unpack_from('<2I', data, field)
    if start + count * 16 > len(data):
        raise ValueError('M2 texture array exceeds file')
    result = []
    for i in range(count):
        p = start + 16 * i
        typ, flags, length, offset = struct.unpack_from('<4I', data, p)
        if typ == 0:
            if not length or offset + length > len(data) or data[offset + length - 1] != 0:
                raise ValueError('Invalid M2 texture string')
            result.append((p, data[offset:offset + length - 1].decode('latin1')))
    return result


def rewrite_m2_textures(data, mapping):
    out = bytearray(data)
    for p, name in m2_textures(data):
        target = mapping.get(key(name), name).encode('latin1') + b'\0'
        struct.pack_into('<2I', out, p + 8, len(target), len(out))
        out.extend(target)
    m2_textures(out)
    return bytes(out)


def validate_skin(data):
    if len(data) < 48 or data[:4] != b'SKIN':
        raise ValueError('Invalid Wrath SKIN header')
    for field, stride in ((4, 2), (12, 2), (20, 4), (28, 48), (36, 24)):
        count, offset = struct.unpack_from('<2I', data, field)
        if count and (offset < 48 or offset + count * stride > len(data)):
            raise ValueError('SKIN array exceeds file')


def rewrite_tile(data, resolve):
    tile = Tile(data)
    bodies = {}
    active = {key(n) for _, _, n in active_textures(tile)}
    for names, ids, kind in (('mmdx', 'mmid', 'm2'), ('mwmo', 'mwid', 'wmo'),
                             ('mtex', None, 'texture')):
        old = tile.body(names)
        new = b''.join((resolve(n.decode('latin1'), kind).encode('latin1')
                        if kind != 'texture' or key(n.decode('latin1')) in active else n) + b'\0'
                       for n in name_offsets(old).values())
        bodies[names] = new
        if ids:
            bodies[ids] = remap_name_table(old, new, tile.body(ids))
    out = bytearray(data[:12] + chunk(b'RDHM', bytes(64)) + chunk(b'NICM', bytes(4096)))
    positions = {'mcin': 84}
    keys = {p: k for k, p in tile.offsets.items() if p}
    for p, end in tile.ends.items():
        if p in (0, 12, tile.offsets['mcin']) or data[p:p + 4] == b'KNCM':
            continue
        k = keys.get(p)
        if k:
            positions[k] = len(out)
        out.extend(chunk(CHUNK_MAGIC[k], bodies[k]) if k in bodies else data[p:end])
    for i, cell in enumerate(tile.cells):
        if cell is not None:
            struct.pack_into('<4I', out, 92 + i * 16, len(out), len(cell), *tile.entries[i][2:])
            out.extend(cell)
        else:
            struct.pack_into('<4I', out, 92 + i * 16, 0, 0, *tile.entries[i][2:])
    header = list(tile.header)
    for j, k in enumerate(MHDR_FIELDS[1:12], 1):
        header[j] = positions[k] - 20 if k in positions else 0
    struct.pack_into('<16I', out, 20, *header)
    rebuilt = Tile(bytes(out))
    if rebuilt.cells != tile.cells:
        raise ValueError('ADT terrain/cell bytes changed')
    for before, after in zip(tile.placements, rebuilt.placements):
        if [r[4:] for _, r in before] != [r[4:] for _, r in after]:
            raise ValueError('ADT placement bytes changed')
    return bytes(out)


def active_textures(tile):
    used = []
    for slot, cell in enumerate(tile.cells):
        if cell is None or not u32(cell, 0x14):
            continue
        p, end = Tile.sub(cell, 0x24, b'YLCM')
        if end - p - 8 != u32(cell, 0x14) * 16:
            raise ValueError('Invalid MCLY layer count')
        for layer, q in enumerate(range(p + 8, end, 16)):
            index = u32(cell, q)
            if index >= len(tile.textures):
                raise ValueError('MCLY texture index outside MTEX')
            used.append((slot, layer, tile.textures[index].decode('latin1')))
    return used


def residual_layer_impact(tile, slot, layer):
    """Measure legacy 4-bit alpha without inventing replacement texture pixels.

    This is a proposal for the terrain owner, never an implicit layer deletion.
    The 64x64 estimates include the stored last row/column; edge-fix sampling in
    the client can differ. Upper layers attenuate earlier layers sequentially.
    """
    cell = tile.cells[slot]
    p, end = Tile.sub(cell, 0x24, b'YLCM')
    records = [struct.unpack_from('<4I', cell, q) for q in range(p + 8, end, 16)]
    if not 0 < layer < len(records):
        raise ValueError('Only non-base residual layers can be measured')
    a, b = Tile.sub(cell, 0x2C, b'LACM')
    alpha = cell[a + 8:b]
    arrays = {}
    for i in range(1, len(records)):
        _, flags, offset, _ = records[i]
        limit = records[i + 1][2] if i + 1 < len(records) else len(alpha)
        if flags & 0x200 or not flags & 0x100 or limit - offset != 2048:
            raise ValueError('Impact proposal only supports explicit uncompressed 4-bit alpha')
        arrays[i] = [v for byte in alpha[offset:limit] for v in (byte & 15, byte >> 4)]
    values = arrays[layer]
    effective = [v / 15 for v in values]
    for i in range(layer + 1, len(records)):
        effective = [v * (1 - top / 15) for v, top in zip(effective, arrays[i])]
    return {'format': 'legacy-uncompressed-4bit', 'samples': len(values),
            'alpha_sha256': digest(alpha[records[layer][2]:records[layer][2] + 2048]),
            'histogram_4bit': dict(sorted(Counter(values).items())),
            'nonzero_samples': [{'x': i % 64, 'y': i // 64, 'alpha_8bit': v * 17,
                                 'effective_weight': effective[i]} for i, v in enumerate(values) if v],
            'mean_alpha_8bit': sum(values) * 17 / len(values), 'max_alpha_8bit': max(values) * 17,
            'mean_effective_weight': sum(effective) / len(values), 'max_effective_weight': max(effective),
            'equivalent_full_opacity_area_square_yards': sum(effective) / len(values) * (100 / 3) ** 2,
            'proposal': 'Explicitly remove this residual error layer and its 2048 alpha bytes in terrain composition, rebuild MCLY/MCAL and cell offsets, remove unused MTEX/MTXF slot and reindex MCLY. Preserve other layers, height, objects, water, normals and shadows. No texture substitution.',
            'applied': False, 'owner': 'terrain principal',
            'estimate_caveat': 'Stored 64x64 alpha samples; not a rendered pixel-area or screenshot comparison.'}


def validate_blp(data):
    if len(data) < 148 or data[:4] not in (b'BLP1', b'BLP2'):
        raise ValueError('Invalid BLP header')
    width, height = struct.unpack_from('<2I', data, 12)
    if not width or not height or width & (width - 1) or height & (height - 1):
        raise ValueError('Invalid BLP dimensions')
    start = 28 if data[:4] == b'BLP1' else 20
    offsets = struct.unpack_from('<16I', data, start)
    sizes = struct.unpack_from('<16I', data, start + 64)
    if not offsets[0] or not sizes[0]:
        raise ValueError('BLP has no base mip')
    for i, (p, n) in enumerate(zip(offsets, sizes)):
        if i and (width >> i == 0 or height >> i == 0):
            break  # Inactive legacy descriptors do not describe image data.
        if bool(p) != bool(n) or (p and p + n > len(data)):
            raise ValueError('BLP active mip exceeds file')
    return {'format': data[:4].decode(), 'width': width, 'height': height,
            'encoding': u32(data, 4) if data[:4] == b'BLP1' else data[8]}


class Closure:
    def __init__(self, native, source, output, dotnet, converter, liquid_policy=None):
        self.native, self.source, self.output = native, source, output
        self.dotnet, self.converter = dotnet, converter
        self.resources, self.blockers, self.edges, self.files = {}, [], [], {}
        self.context = 'ADT'
        policy = (json.loads(WMO_LIQUID_MANIFEST.read_text()) if liquid_policy is None
                  else liquid_policy)
        self.liquid_policy = {key(r['source']): r for r in policy['families']}

    def block(self, name, reason, remedy):
        item = {'resource': name, 'reason': reason, 'remedy': remedy}
        if item not in self.blockers:
            self.blockers.append(item)

    def emit(self, name, data, provenance, adaptation):
        name = client_path(name)
        k = key(name)
        if k in self.files and self.files[k]['sha256'] != digest(data):
            raise ValueError('Output collision: ' + name)
        path = self.output / 'files' / name.replace('\\', '/')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.files[k] = {'path': name, 'sha256': digest(data), 'bytes': len(data),
                         'provenance': provenance, 'adaptation': adaptation}
        return path

    def resolve(self, name, kind, snapshot=None):
        name = model_path(name) if kind == 'm2' else client_path(name)
        scope = snapshot or 'prefer-native'
        k = scope + ':' + key(name)
        self.edges.append({'parent': self.context, 'resource_id': k, 'source': name, 'kind': kind, 'scope': scope})
        if k in self.resources:
            return self.resources[k]['target']
        entry = {'id': k, 'source': name, 'kind': kind, 'target': name, 'status': 'resolving', 'dependencies': []}
        self.resources[k] = entry
        parent = self.context
        self.context = k
        try:
            found = self.native.get(name) if snapshot != 'turtle' else None
            native = found is not None
            if found is None and snapshot != '335':
                found = self.source.get(name)
            if found is None:
                raise ValueError('Missing in explicit snapshots (including direct MPQ probes)')
            data, provenance = found
            entry['provenance'] = provenance
            if not native:
                entry['target'] = isolated(name)
            target = entry['target']
            if kind == 'texture':
                entry['blp'] = validate_blp(data)
                if not native:
                    self.emit(target, data, provenance, 'byte-exact source texture')
            elif kind == 'wmo':
                self.wmo(entry, data, native)
            elif kind == 'm2':
                self.m2(entry, data, native)
            elif kind == 'skin':
                validate_skin(data)
            else:
                if not native:
                    raise ValueError('Unsupported custom dependency: ' + kind)
            entry['status'] = ('blocked' if entry.get('semantic_blocked') else
                               'native-reuse' if native else 'staged')
        except (ValueError, OSError, struct.error, KeyError) as exc:
            entry['status'] = 'blocked'
            entry['error'] = str(exc)
            self.block(name, str(exc), 'Recover the exact source payload/dependencies or extend and validate the existing format converter; rerun into a fresh directory.')
        finally:
            self.context = parent
        return entry['target']

    def finalize(self):
        """Do not call an emitted parent complete when a child failed."""
        for identity, entry in self.resources.items():
            entry['dependency_ids'] = sorted({e['resource_id'] for e in self.edges if e['parent'] == identity})
        changed = True
        while changed:
            changed = False
            for entry in self.resources.values():
                missing = [d for d in entry['dependency_ids']
                           if self.resources[d]['status'] in ('blocked', 'incomplete')]
                if missing and entry['status'] not in ('blocked', 'incomplete'):
                    entry['status'] = 'incomplete'
                    changed = True
                entry['unresolved_dependency_ids'] = missing

    def wmo(self, entry, data, native):
        bodies = dict(wmo_chunks(data))
        if len(bodies.get('MOHD', b'')) != 64:
            raise ValueError('Invalid WMO root MOHD')
        groups = u32(bodies['MOHD'], 4)
        if len(bodies.get('MOGI', b'')) != groups * 32:
            raise ValueError('WMO group count/MOGI mismatch')
        # Reuse a native family as a unit; do not fill a native hole from Turtle.
        reader = self.native if native else self.source
        group_records, group_payloads = [], []
        for i in range(groups):
            source = entry['source'][:-4] + f'_{i:03}.wmo'
            found = reader.get(source)
            if found is None:
                raise ValueError('Missing WMO group: ' + source)
            raw, provenance = found
            group_payloads.append((source, raw))
            cs = dict(wmo_chunks(raw))
            if 'MOGP' not in cs or len(cs['MOGP']) < 68:
                raise ValueError('Invalid WMO group MOGP: ' + source)
            # MOGP's nested chunks are not modified; indices/geometry stay exact.
            group_records.append({'source': source, 'provenance': provenance,
                                  'group_id': u32(cs['MOGP'], 56)})
        if not native:
            policy = self.liquid_policy.get(key(entry['source']))
            if policy is not None:
                data, entry['liquid_adaptation'] = adapt_wmo_dry_liquids(
                    data, entry['source'], group_payloads, policy)
            for i, ((_, raw), record) in enumerate(zip(group_payloads, group_records)):
                self.emit(entry['target'][:-4] + f'_{i:03}.wmo', raw, record['provenance'],
                          'byte-exact v17 group; coherent source family')
        if native:
            # Verify native transitive dependencies without modifying the family.
            for table, kind in (('MOTX', 'texture'), ('MODN', 'm2')):
                for name in strings(bodies.get(table, b'')).values():
                    self.resolve(name, kind, '335')
            dependencies = []
        else:
            adaptations = []
            rewritten, dependencies = rewrite_wmo(data, self.resolve, adaptations)
            entry['material_adaptations'] = adaptations
            sky = bodies.get('MOSB', b'').split(b'\0', 1)[0]
            if sky:
                target = self.resolve(sky.decode('latin1'), 'm2')
                rewritten_bodies = dict(wmo_chunks(rewritten))
                rewritten_bodies['MOSB'] = target.encode('latin1') + b'\0'
                rewritten = b''.join(chunk(n.encode()[::-1], rewritten_bodies[n])
                                     for n, _ in wmo_chunks(rewritten))
            self.emit(entry['target'], rewritten, entry['provenance'],
                      'v17 MOTX/MODN/MOSB strings + MOMT/MODD offsets; geometry/group identity unchanged' +
                      ('; hash-locked dry-family MOHD.flags & ~0x4' if policy else ''))
            if policy:
                entry['liquid_adaptation']['staged_audit'] = wmo_liquid_audit(rewritten, group_payloads)
        entry.update(groups=group_records, dependencies=dependencies, version=17)
        sky = bodies.get('MOSB', b'').split(b'\0', 1)[0]
        if sky and native:
            self.resolve(sky.decode('latin1'), 'm2', '335')

    def m2(self, entry, data, native):
        textures = m2_textures(data)
        version = u32(data, 4)
        entry['version'] = version
        if native:
            if version != 264:
                raise ValueError('Native path is not a Wrath v264 M2')
            count, offset = struct.unpack_from('<2I', data, 80)
            if any(u32(data, offset + i * 16) for i in range(count)):
                raise ValueError('Native static doodad requires explicit replaceable texture bindings')
            for _, name in textures:
                self.resolve(name, 'texture', '335')
            views = u32(data, 68)
            for i in range(views):
                self.resolve(entry['source'][:-3] + f'{i:02}.skin', 'skin', '335')
            count, offset = struct.unpack_from('<2I', data, 28)
            if offset + count * 64 > len(data):
                raise ValueError('M2 sequences exceed file')
            for i in range(count):
                p = offset + i * 64
                flags = u32(data, p + 12)
                if not flags & (0x20 | 0x40 | 0x100):
                    anim, variation = struct.unpack_from('<2H', data, p)
                    self.resolve(entry['source'][:-3] + f'{anim:04}-{variation:02}.anim', 'anim', '335')
            count, offset = struct.unpack_from('<2I', data, 296)
            if offset + count * 476 > len(data):
                raise ValueError('M2 particle array exceeds file')
            for i in range(count):
                for field in (24, 32):
                    length, p = struct.unpack_from('<2I', data, offset + i * 476 + field)
                    if length:
                        if p + length > len(data) or data[p + length - 1] != 0:
                            raise ValueError('Invalid M2 particle resource string')
                        name = data[p:p + length - 1].decode('latin1')
                        if name:
                            self.resolve(name, 'm2', '335')
            return
        if version != 256:
            raise ValueError('Custom conversion requires v256 input')
        if len(data) < 324:
            raise ValueError('Truncated classic M2 header')
        entry['classic_conversion_blocks'] = {str(p): u32(data, p) for p in (108, 308, 316)}
        resolved_textures = {key(name): self.resolve(name, 'texture') for _, name in textures}
        if not self.dotnet or not self.converter.is_file():
            raise ValueError('Existing C# converter/.NET SDK unavailable')
        input_path = self.output / 'evidence' / (digest(key(entry['source']).encode()) + '.m2')
        input_path.write_bytes(data)
        output_path = self.output / 'evidence' / ('converted-' + input_path.name)
        args = [self.dotnet, self.converter, 'convert', '--source', input_path,
                '--output', output_path, '--namespace', NS]
        targets = {}
        for _, name in textures:
            mapped = NS + '\\Textures\\he_' + digest(key(name).encode())[:20] + '.blp'
            if key(name) not in targets:
                args += ['--texture-map', name + '=' + mapped]
                targets[key(name)] = mapped
        result = run(args)
        log = output_path.with_suffix('.log')
        log.write_text(result.stdout + result.stderr)
        entry['conversion_log'] = str(log.relative_to(self.output))
        if result.returncode:
            raise ValueError('C# conversion rejected model: ' + (result.stderr.splitlines()[0] if result.stderr else str(result.returncode)))
        report = json.loads(Path(str(output_path) + '.report.json').read_text())
        entry['conversion'] = report
        if not report['fullySupported']:
            entry['semantic_blocked'] = True
            self.block(entry['source'], 'Converter reports unsupported semantics: ' + json.dumps(report['unsupportedSemantics']),
                       'Implement and independently validate those semantics in the existing converter before acceptance.')
        mapping = {}
        for resource in report['hardcodedResources']:
            mapping[key(resource['target'])] = resolved_textures[key(resource['source'])]
        converted = rewrite_m2_textures(output_path.read_bytes(), mapping)
        if u32(converted, 4) != 264:
            raise ValueError('Converter did not emit v264')
        self.emit(entry['target'], converted, entry['provenance'],
                  'existing C# v256->v264 converter; type-0 strings repointed to resolved assets')
        for i in range(report['skins']):
            skin = output_path.with_name(output_path.stem + f'{i:02}.skin')
            raw = skin.read_bytes()
            validate_skin(raw)
            self.emit(entry['target'][:-3] + f'{i:02}.skin', raw, entry['provenance'],
                      'external skin generated by existing converter')
        # Replaceable textures require a separate explicit appearance binding;
        # ADT/WMO static doodads have no creature-display/CharSections context.
        count, offset = struct.unpack_from('<2I', data, 92)
        types = [u32(data, offset + i * 16) for i in range(count)]
        if any(types):
            entry['semantic_blocked'] = True
            self.block(entry['source'], 'Custom static doodad has replaceable texture types: ' + str(types),
                       'Recover explicit source appearance bindings; do not guess textures from a creature/character DBC.')


def build(args):
    output = args.output.resolve()
    if output.exists():
        raise ValueError('Output must be fresh: ' + str(output))
    tiles = sorted(args.terrain.glob('Azeroth_*.adt'))
    if len(tiles) != 24:
        raise ValueError(f'Expected 24 terrain candidates, found {len(tiles)}')
    # Validate inputs before creating the staging tree.
    for path in tiles:
        active_textures(Tile(path.read_bytes()))
    output.mkdir(parents=True)
    evidence = output / 'evidence'
    evidence.mkdir()
    reader = build_reader(evidence)
    native = Snapshot(args.native, '335', evidence, args.mpq, args.locale, reader)
    source = Snapshot(args.source, 'turtle', evidence, args.mpq, args.locale, reader)
    closure = Closure(native, source, output, args.dotnet, args.converter)
    # The build wrapper pins both source and binary hashes and does not rebuild
    # or modify the converter in --validate mode.
    env = dict(os.environ, DOTNET=args.dotnet or 'dotnet')
    validation = subprocess.run([str(ROOT / 'scripts/build-new-races-model-converter.sh'), '--validate'],
                                env=env, capture_output=True, text=True)
    (evidence / 'converter-validation.log').write_text(validation.stdout + validation.stderr)
    if validation.returncode:
        closure.dotnet = None
        closure.block('converter', 'Existing converter validation failed',
                      'Build/restore the pinned converter with scripts/build-new-races-model-converter.sh and set --dotnet to its .NET 8 SDK.')
    error_uses, terrain_records = [], []
    for path in tiles:
        data = path.read_bytes()
        tile = Tile(data)
        for slot, layer, name in active_textures(tile):
            if key(name).rsplit('\\', 1)[-1] in ('error_1.blp', 'error_2.blp'):
                try:
                    impact = residual_layer_impact(tile, slot, layer)
                except ValueError as exc:
                    impact = {'error': str(exc), 'applied': False}
                error_uses.append({'tile': path.name, 'cell': slot, 'layer': layer, 'name': name,
                                   'impact': impact, 'cell_sha256': digest(tile.cells[slot])})
        closure.context = path.name
        rewritten = rewrite_tile(data, closure.resolve)
        target = 'World\\Maps\\Azeroth\\' + path.name
        provenance = {'path': str(path.resolve()), 'sha256': digest(data)}
        closure.emit(target, rewritten, provenance, 'ADT name tables + MMID/MWID/MHDR/MCIN offsets; cells and placements byte-preserved')
        terrain_records.append({'source': provenance, 'target': target, 'sha256': digest(rewritten)})
    # Look for exact-name source art and its provenance, never aliases by visual
    # resemblance. The research extraction is compared to the actual source ADT.
    investigation = {'active_uses': error_uses, 'exact_basename_candidates': [], 'source_tiles': []}
    if error_uses:
        for snapshot in (source, native):
            for name in sorted(snapshot.index):
                if name.rsplit('\\', 1)[-1] in ('error_1.blp', 'error_2.blp'):
                    found = snapshot.get(name)
                    investigation['exact_basename_candidates'].append({'name': name, 'provenance': found[1] if found else None})
        for filename in sorted({r['tile'] for r in error_uses}):
            found = source.get('World\\Maps\\Azeroth\\' + filename)
            if found:
                source_data, provenance = found
                research = args.research / 'turtle' / 'World' / 'Maps' / 'Azeroth' / filename
                research_hash = digest(research.read_bytes()) if research.is_file() else None
                source_tile = Tile(source_data)
                uses = [{'cell': slot, 'layer': layer, 'texture': name}
                        for slot, layer, name in active_textures(source_tile)
                        if slot in {r['cell'] for r in error_uses if r['tile'] == filename}]
                investigation['source_tiles'].append({'tile': filename, 'provenance': provenance,
                                                       'research_sha256': research_hash, 'layers': uses})
        for name in sorted({r['name'] for r in error_uses}):
            remedy = ('Terrain principal can explicitly remove the measured residual error layer '
                      '(see error_texture_investigation), or recover intended art from the author. '
                      'Rebuild candidate; do not substitute textures.')
            existing = next((b for b in closure.blockers if b['resource'] == name), None)
            if existing:
                existing['reason'] += '; active original-source terrain error layer'
                existing['remedy'] = remedy
            else:
                closure.block(name, 'Active terrain error layer; intended artwork not established', remedy)
    closure.finalize()
    native_basenames = {name.rsplit('\\', 1)[-1] for name in native.index if name.endswith(('.m2', '.wmo'))}
    custom_basenames = set()
    for name in closure.files:
        if name.endswith(('.m2', '.wmo')):
            base = name.rsplit('\\', 1)[-1]
            if base in native_basenames or base in custom_basenames or name in native.index:
                closure.block(name, 'Namespace/VMap flattened basename collision', 'Choose a collision-free isolated namespace/basename and rebuild all references.')
            custom_basenames.add(base)
    research_files = {}
    for kind in ('turtle', '335'):
        for path in (args.research / kind).rglob('*'):
            if path.is_file():
                name = key(str(path.relative_to(args.research / kind)))
                research_files[(kind, name)] = path
    for entry in closure.resources.values():
        records = [entry] + entry.get('groups', [])
        for record in records:
            provenance = record.get('provenance')
            if not provenance:
                continue
            kind = '335' if provenance.get('snapshot') == str(native.root) else 'turtle'
            path = research_files.get((kind, key(record['source'])))
            if path:
                sha = file_hash(path)
                record['research'] = {'path': str(path), 'sha256': sha,
                                      'matches_live_snapshot': sha == provenance['sha256']}
    manifest = {'schema': 1, 'status': 'offline-assets-candidate', 'apply_ready': False,
                'asset_closure_complete': not closure.blockers, 'tiles': terrain_records,
                'resources': list(closure.resources.values()), 'edges': closure.edges,
                'files': sorted(closure.files.values(), key=lambda f: f['path'].lower()),
                'blockers': closure.blockers, 'error_texture_investigation': investigation,
                'resolution_policy': {'native': str(args.native), 'source': str(args.source),
                                      'locale': args.locale, 'priority': 'explicit fresh archive order; direct probes; native preferred; native families never filled from source',
                                      'native_runtime': 'NOT RUN', 'mpq_deployment': 'NOT PERFORMED'},
                'archives': {'335': native.provenance(), 'turtle': source.provenance()},
                'converter': {'path': str(args.converter), 'sha256': file_hash(args.converter) if args.converter.is_file() else None,
                              'validation': 'PASS' if not validation.returncode else 'FAIL'},
                'builder_sha256': file_hash(Path(__file__)),
                'wmo_liquid_policy': {'path': str(WMO_LIQUID_MANIFEST),
                                      'sha256': file_hash(WMO_LIQUID_MANIFEST)},
                'reader': {'source_sha256': digest(READER_CPP.encode()), 'binary_sha256': file_hash(reader),
                           'stormlib_sha256': file_hash(ROOT / 'tools/stormlib/lib/libstorm.a')},
                'remaining_gates': ['Input terrain candidate is not apply-ready; preserve its existing liquid/border/DBC gates.',
                                    'Client rendering, collision/VMap extraction and navigation have NOT RUN.']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    native.close()
    source.close()
    print(json.dumps({'output': str(output), 'apply_ready': False, 'files': len(closure.files),
                      'resources': len(closure.resources), 'states': dict(Counter(r['status'] for r in closure.resources.values())),
                      'blockers': len(closure.blockers)}, indent=2))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terrain', type=Path, default=ROOT / 'work/high-elf-terrain-candidate')
    parser.add_argument('--research', type=Path, default=ROOT / 'work/elf-map-audit-research')
    parser.add_argument('--source', type=Path, default=Path('/home/dev/wow-turtle'))
    parser.add_argument('--native', type=Path, default=Path('/home/dev/wow-335'))
    parser.add_argument('--output', type=Path, default=ROOT / 'work/high-elf-assets-candidate')
    parser.add_argument('--locale', default='esES', choices=('esES', 'enUS'))
    parser.add_argument('--mpq', type=Path, default=ROOT / 'tools/mpq')
    parser.add_argument('--dotnet', default=shutil.which('dotnet'))
    parser.add_argument('--converter', type=Path, default=ROOT / 'work/toolchains/new-races-model-converter/NewRacesModelConverter.dll')
    args = parser.parse_args()
    build(args)


if __name__ == '__main__':
    main()
