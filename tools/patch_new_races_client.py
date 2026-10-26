#!/usr/bin/env python3
"""Generate pinned private cache/optional local-GlueXML PE derivatives."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT / 'patches/client/new-races-cache.json'
SOURCE_SHA = 'bf644876709c591acc17c0da8cdf1814edcc9f1e6bc109a8c0d5c38c79dc953c'
OUTPUT_SHA = 'cf11d2794fc4a568f80150f2bf57a3d076d6e79e33b563e26075388477d60c2a'
CUSTOM_GLUE_SHA = '87ceca9ea08da2f0d9d312d833ae76751a3ab8f2b8a7d742bfd2356e55f291f3'
PROTECTED = (Path('/home/dev/wow-335'), Path('/home/dev/wow-turtle'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_output(output, source=None):
    output = Path(output).resolve()
    require(source is None or output != Path(source).resolve(), 'Output equals input')
    for root in PROTECTED:
        require(not output.is_relative_to(root.resolve()), 'Output in original client directory')
    if source is not None:
        require(not output.is_relative_to(Path(source).resolve().parent),
                'Output must be outside the source executable directory')
    require(not output.exists(), 'Output already exists (no overwrite)')
    return output


def parse_pe(data):
    require(data[:2] == b'MZ', 'Not DOS/PE')
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    require(data[pe:pe+4] == b'PE\0\0', 'Invalid PE signature')
    machine, count, _, _, _, opt_size, flags = struct.unpack_from('<HHIIIHH', data, pe+4)
    opt = pe + 24
    require(machine == 0x14c and struct.unpack_from('<H', data, opt)[0] == 0x10b,
            'Only i386 PE32 supported')
    require(opt_size >= 224, 'Short optional header')
    imagebase, section_align, file_align = struct.unpack_from('<III', data, opt+28)
    dll_flags = struct.unpack_from('<H', data, opt+70)[0]
    reloc = struct.unpack_from('<II', data, opt+96+5*8)
    require(not dll_flags & 0x40 and reloc == (0, 0), 'Expected fixed image without relocations')
    sections = []
    for i in range(count):
        off = opt + opt_size + i*40
        name, vs, rva, rs, raw, _, _, _, _, chars = struct.unpack_from('<8sIIIIIIHHI', data, off)
        require(raw+rs <= len(data), 'Section extends beyond file')
        sections.append(dict(name=name.rstrip(b'\0').decode('ascii'), virtual_size=vs,
                             rva=rva, raw_size=rs, raw_offset=raw, characteristics=chars))
    return dict(image_base=imagebase, section_alignment=section_align, file_alignment=file_align,
                size_of_image=struct.unpack_from('<I', data, opt+56)[0],
                checksum_offset=opt+64, checksum=struct.unpack_from('<I', data, opt+64)[0],
                sections=sections, coff_flags=flags)


def pe_checksum(data, offset):
    total = 0
    for pos in range(0, len(data), 2):
        word = 0 if offset <= pos < offset+4 else int.from_bytes(data[pos:pos+2], 'little')
        total += word
        total = (total & 0xffff) + (total >> 16)
    total = (total & 0xffff) + (total >> 16)
    return total + len(data)


def patch_bytes(data, plan=None, allow_custom_gluexml=False):
    plan = json.loads(PIN.read_text()) if plan is None else plan
    require(sha(data) == SOURCE_SHA == plan['input_sha256'], 'Unknown input SHA256 (or already patched)')
    require(len(data) == plan['input_size'], 'Wrong source size')
    before = parse_pe(data)
    for label in ('validator_call', 'result_dispatch'):
        evidence = plan['integrity'][label]
        offset = int(evidence['file_offset'], 0)
        expected_bytes = bytes.fromhex(evidence['bytes'])
        require(data[offset:offset+len(expected_bytes)] == expected_bytes,
                'GlueXML static integrity evidence mismatch')
    require(before['image_base'] == 0x400000, 'Unexpected image base')
    require(max(s['raw_offset']+s['raw_size'] for s in before['sections']) == len(data), 'Unexpected overlay')
    old_base = bytes.fromhex('d0 b0 b6 00')
    actual = {i for i in range(len(data)-3) if data[i:i+4] == old_base}
    expected = {int(e['file_offset'], 0) for e in plan['edits'] if bytes.fromhex(e['original']) == old_base}
    require(len(expected) == 8 and actual == expected, 'Eight old cache references must match proposal exactly')
    result = bytearray(data)
    allowed = set()
    for edit in plan['edits']:
        off = int(edit['file_offset'], 0)
        old, new = bytes.fromhex(edit['original']), bytes.fromhex(edit['replacement'])
        require(len(old) == len(new) and data[off:off+len(old)] == old, 'Proposal old-byte mismatch')
        region = set(range(off, off+len(old)))
        require(not allowed & region, 'Overlapping proposal edits')
        allowed.update(region)
        result[off:off+len(new)] = new
    append = plan['append']
    require(int(append['file_offset'], 0) == len(data) and append['length'] == 512 and append['byte'] == 0,
            'Unexpected append extent')
    result.extend(bytes(512))
    after = parse_pe(result)
    section = after['sections'][-1]
    require(section == dict(name='.nraces', virtual_size=0xc0, rva=0x9fd000,
                            raw_size=0x200, raw_offset=len(data), characteristics=0xc0000040),
            'Incorrect RW non-executable 48-pointer section')
    require(after['sections'][:-1] == before['sections'] and after['size_of_image'] == 0x9fe000,
            'Existing sections changed')
    require(pe_checksum(result, after['checksum_offset']) == after['checksum'], 'PE checksum mismatch')
    require(len(result) == plan['output_size'] and sha(result) == OUTPUT_SHA == plan['proposed_output_sha256'],
            'Derivative does not match authoritative recipe')
    require(all(a == b or i in allowed for i, (a, b) in enumerate(zip(data, result))), 'Unexpected byte changes')
    report = dict(input_sha256=sha(data), output_sha256=sha(result),
                               section=section, checksum=after['checksum'], edits=plan['edits'],
                               original_unchanged=True, windows_startup='NOT RUN',
                               modified_GlueXML_acceptance='NOT RUN', integrity_bypass='NONE',
                               integrity_static=plan['integrity'],
                               account_server_authentication='unchanged')
    report['profile'] = 'cache-only'
    report['gluexml_static_gate'] = 'STRICT: modified XML/Lua graph digest is rejected'
    if allow_custom_gluexml:
        profile = plan['custom_gluexml_profile']
        for guard in profile['guards']:
            offset = int(guard['file_offset'], 0)
            expected_bytes = bytes.fromhex(guard['bytes'])
            require(data[offset:offset+len(expected_bytes)] == expected_bytes,
                    'Custom GlueXML control-flow guard mismatch: ' + guard['meaning'])
        cache_only = bytes(result)
        profile_allowed = set()
        for edit in profile['edits_from_cache']:
            offset = int(edit['file_offset'], 0)
            old, new = bytes.fromhex(edit['original']), bytes.fromhex(edit['replacement'])
            require(len(old) == len(new) and cache_only[offset:offset+len(old)] == old,
                    'Custom GlueXML old-byte mismatch')
            require(not profile_allowed.intersection(range(offset, offset+len(old))),
                    'Overlapping custom GlueXML edits')
            profile_allowed.update(range(offset, offset+len(old)))
            result[offset:offset+len(new)] = new
        custom_pe = parse_pe(result)
        require(custom_pe['sections'] == after['sections'], 'Custom GlueXML changed sections')
        require(pe_checksum(result, custom_pe['checksum_offset']) == custom_pe['checksum'],
                'Custom GlueXML checksum mismatch')
        require(all(a == b or i in profile_allowed for i, (a,b) in enumerate(zip(cache_only, result))),
                'Unexpected custom GlueXML byte changes')
        require(len(result) == len(cache_only) and sha(result) == CUSTOM_GLUE_SHA == profile['output_sha256'],
                'Custom GlueXML endpoint mismatch: ' + sha(result))
        report.update(profile='cache-plus-custom-gluexml', output_sha256=sha(result),
                      checksum=custom_pe['checksum'],
                      gluexml_static_gate='ALLOW status2 content digest mismatch; missing/invalid signature still rejected',
                      integrity_bypass='OPT-IN local GlueXML content digest mismatch only',
                      custom_gluexml=profile)
    return bytes(result), report


def build(source, output, allow_custom_gluexml=False):
    source = Path(source).resolve()
    output = safe_output(output, source)
    report_path = safe_output(output.with_suffix('.report.json'), source)
    original = source.read_bytes()
    result, report = patch_bytes(original, allow_custom_gluexml=allow_custom_gluexml)
    require(source.read_bytes() == original, 'Source changed during generation')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as handle:
        handle.write(result)
    report.update(input=str(source), output=str(output))
    with report_path.open('x') as handle:
        json.dump(report, handle, indent=2)
        handle.write('\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('/home/dev/wow-335/Wow.exe'))
    parser.add_argument('--output', type=Path, default=ROOT / 'out/Wow-new-races.exe')
    parser.add_argument('--allow-custom-gluexml', action='store_true',
                        help='Permit local GlueXML content changes after valid TOC signature; no auth/Warden/network changes')
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.input, args.output, args.allow_custom_gluexml), indent=2))
    except (ValueError, OSError, struct.error) as error:
        parser.exit(1, f'error: {error}\n')


if __name__ == '__main__':
    main()
