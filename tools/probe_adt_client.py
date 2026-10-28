#!/usr/bin/env python3
"""Execute the hash-pinned 3.3.5a x86 MCNK scanner in Unicorn, offline.

Install probe-adt-client-requirements.txt in an isolated venv, or supply an
isolated dependency directory through PYTHONPATH. No client process is launched.
Exit 0 means every cell returned, stayed in bounds and visited only known tags;
exit 1 means validation failed; exit 2 means invalid inputs/setup.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

import pefile
import unicorn
from unicorn import (Uc, UcError, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE,
                     UC_HOOK_MEM_INVALID)
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX,
                               UC_X86_REG_EDX, UC_X86_REG_ESI, UC_X86_REG_EDI,
                               UC_X86_REG_EBP, UC_X86_REG_ESP, UC_X86_REG_EIP,
                               UC_X86_REG_EFLAGS)

from adt import _adt_layout
from adt_client import KNOWN

START, END = 0x7C3A10, 0x7C3B3C  # exclusive end
FUNCTION_SHA256 = 'c5c8779e6e404d3fa2c62f221ca3e91de4414d3d130f50dea3ed644af88ea5f6'
REGISTERS = dict(eax=UC_X86_REG_EAX, ebx=UC_X86_REG_EBX, ecx=UC_X86_REG_ECX,
                 edx=UC_X86_REG_EDX, esi=UC_X86_REG_ESI, edi=UC_X86_REG_EDI,
                 ebp=UC_X86_REG_EBP, esp=UC_X86_REG_ESP)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Probe:
    """Minimal thiscall object, isolated cell copy and synthetic return stack.

    Hooks observe real dispatch and effective sizes after native fixups. They
    do not repair inputs or stop bad tag walks, so original faults remain visible.
    Only the pinned function is executable; any code escape stops the call.
    """
    obj, blob, stack, stop = 0x1000000, 0x1100000, 0x1208000, 0x1210000
    capacity = 0x10000

    def __init__(self, exe, instruction_limit=100000):
        raw = exe.read_bytes()
        with pefile.PE(data=raw) as pe:
            base = pe.OPTIONAL_HEADER.ImageBase
            if pe.FILE_HEADER.Machine != 0x14C or base != 0x400000:
                raise ValueError('expected x86 PE at image base 0x400000')
            code = pe.get_data(START - base, END - START)
            if len(code) != END - START or sha(code) != FUNCTION_SHA256:
                raise ValueError('scanner function hash mismatch: ' + str(exe))
        self.identity = dict(sha256=sha(raw), function_sha256=sha(code))
        self.limit = instruction_limit
        self.u = u = Uc(UC_ARCH_X86, UC_MODE_32)
        page = START & ~0xFFF
        u.mem_map(page, 0x1000)
        u.mem_write(START, code)
        u.mem_map(self.obj, 0x1000)
        u.mem_map(self.blob, self.capacity)
        u.mem_map(self.stack - 0x8000, 0x10000)
        u.mem_map(self.stop, 0x1000)
        u.hook_add(UC_HOOK_MEM_INVALID, self.on_invalid)
        u.hook_add(UC_HOOK_CODE, self.on_code)

    def on_invalid(self, u, access, address, size, value, _):
        self.invalid.append(dict(eip=hex(u.reg_read(UC_X86_REG_EIP)),
                                 access=access, address=hex(address), size=size,
                                 registers={k: hex(u.reg_read(v)) for k, v in REGISTERS.items()}))
        return False

    def on_code(self, u, address, size, _):
        self.instructions += 1
        if not START <= address < END:
            self.escaped = hex(address)
            u.emu_stop()
        elif address == 0x7C3A42:
            p = u.reg_read(UC_X86_REG_ESI) - self.blob
            self.visits += 1
            if not 136 <= p <= self.length - 8:
                self.bounds.append(dict(kind='header', offset=p))
            else:
                tag = bytes(u.mem_read(self.blob + p, 4))
                if tag not in KNOWN:
                    self.unknown.append(dict(offset=p, tag_hex=tag.hex()))
        elif address == 0x7C3B26:
            p = u.reg_read(UC_X86_REG_ESI) - self.blob
            if 136 <= p <= self.length - 8:
                size = struct.unpack('<I', u.mem_read(self.blob + p + 4, 4))[0]
                if p + 8 + size > self.length:
                    self.bounds.append(dict(kind='extent', offset=p, size=size))

    def call(self, cell):
        if not 136 <= len(cell) <= self.capacity:
            raise ValueError('MCNK outside supported 136..65536-byte probe capacity')
        self.length = len(cell)
        self.invalid, self.unknown, self.bounds = [], [], []
        self.instructions = self.visits = 0
        self.escaped = None
        u = self.u
        u.mem_write(self.obj, bytes(0x1000))
        u.mem_write(self.blob, cell + bytes(self.capacity - len(cell)))
        u.mem_write(self.stack - 0x8000, bytes(0x10000))
        u.mem_write(self.obj + 0x10C, struct.pack('<I', self.blob))
        u.mem_write(self.stack, struct.pack('<II', self.stop, 1))
        for register in REGISTERS.values():
            u.reg_write(register, 0)
        u.reg_write(UC_X86_REG_EFLAGS, 2)
        u.reg_write(UC_X86_REG_ESP, self.stack)
        u.reg_write(UC_X86_REG_ECX, self.obj)
        error = None
        try:
            u.emu_start(START, self.stop, count=self.limit)
        except UcError as exc:
            error = str(exc)
        returned = u.reg_read(UC_X86_REG_EIP) == self.stop
        cursor = u.reg_read(UC_X86_REG_EDX) - self.blob
        if returned and cursor != len(cell):
            self.bounds.append(dict(kind='final_cursor', offset=cursor, expected=len(cell)))
        if returned and u.reg_read(UC_X86_REG_ESP) != self.stack + 8:
            self.bounds.append(dict(kind='return_stack'))
        return dict(returned=returned, invalid=self.invalid, unknown=self.unknown,
                    bounds=self.bounds, error=error, code_escape=self.escaped,
                    instruction_limit_reached=not returned and self.instructions >= self.limit,
                    instructions=self.instructions, tag_visits=self.visits)


def run(paths, executables, limit):
    cells, hashes = [], {}
    for path in paths:
        raw = path.read_bytes()
        hashes[path.name] = sha(raw)
        _, _, _, entries, ends = _adt_layout(raw)
        for slot, (offset, *_) in enumerate(entries):
            if offset:
                cells.append((path.name, slot, offset, raw[offset:ends[offset]]))
    if not cells:
        raise ValueError('no populated MCNK cells')
    report = dict(schema=1, observed_at=datetime.now(timezone.utc).isoformat(),
                  mode='native_x86_legacy_fix_1', tiles=len(paths), cells=len(cells),
                  adt_sha256=hashes, dependencies=dict(pefile=pefile.__version__,
                                                     unicorn=unicorn.__version__),
                  instruction_limit_per_call=limit, executables={})
    for exe in executables:
        probe = Probe(exe, limit)
        counts, failures = Counter(), []
        for name, slot, offset, cell in cells:
            result = probe.call(cell)
            good = (result['returned'] and not any(result[k] for k in
                    ('invalid', 'unknown', 'bounds', 'error', 'code_escape')))
            counts.update(calls=1, returned=result['returned'], passed=good,
                          native_faults=bool(result['invalid']),
                          unknown_tag_cells=bool(result['unknown']),
                          out_of_bounds_cells=bool(result['bounds']),
                          instruction_limit_cells=result['instruction_limit_reached'],
                          tag_visits=result['tag_visits'])
            if not good:
                failures.append(dict(tile=name, slot=slot, cell_offset=offset,
                                     cell_size=len(cell), **result))
        report['executables'][str(exe)] = dict(**probe.identity, counts=dict(counts),
                                              failures=failures, passed=not failures)
    report['passed'] = all(r['passed'] for r in report['executables'].values())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adt-dir', type=Path, required=True,
                        help='ADT directory; with --mpq its filenames define the extraction scope')
    parser.add_argument('--exe', type=Path, action='append', required=True,
                        help='x86 client executable (repeatable)')
    parser.add_argument('--output', type=Path, required=True, help='JSON evidence path')
    parser.add_argument('--mpq', type=Path, help='read scoped ADTs from this archive instead')
    parser.add_argument('--mpq-tool', type=Path, default=Path(__file__).with_name('mpq'))
    parser.add_argument('--instruction-limit', type=int, default=100000)
    args = parser.parse_args()
    try:
        paths = sorted(args.adt_dir.glob('*.adt'))
        if not paths or args.instruction_limit < 1:
            raise ValueError('ADT scope must be nonempty and instruction limit positive')
        protected = [*paths, *args.exe, *([args.mpq] if args.mpq else [])]
        if args.output.resolve() in {p.resolve() for p in protected}:
            raise ValueError('output must not overwrite an input')
        with tempfile.TemporaryDirectory(prefix='probe-adt-') as temp:
            source = dict(adt_dir=str(args.adt_dir.resolve()))
            if args.mpq:
                source.update(mpq=str(args.mpq.resolve()), mpq_sha256=sha(args.mpq.read_bytes()))
                extracted = []
                for path in paths:
                    dest = Path(temp) / path.name
                    subprocess.run([str(args.mpq_tool.resolve()), 'extract-one', str(args.mpq),
                                    'World\\Maps\\Azeroth\\' + path.name, str(dest)],
                                   check=True, capture_output=True)
                    extracted.append(dest)
                paths = extracted
            report = run(paths, [p.resolve() for p in args.exe], args.instruction_limit)
            report['source'] = source
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n')
    except (ValueError, OSError, pefile.PEFormatError, subprocess.CalledProcessError) as exc:
        parser.exit(2, 'probe setup/input error: %s\n' % exc)
    for exe, result in report['executables'].items():
        print(exe, json.dumps(result['counts']), 'PASS' if result['passed'] else 'FAIL')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
