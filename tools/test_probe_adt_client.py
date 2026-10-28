"""Native probe contracts. Set ADT_PROBE_EXE to a hash-compatible x86 PE.

Requires probe-adt-client-requirements.txt; never changes the supplied EXE.
"""
import os
from pathlib import Path
import struct
import tempfile
import unittest

import pefile

from probe_adt_client import Probe, START


def cell(body):
    payload = bytes(128) + body
    return b'KNCM' + struct.pack('<I', len(payload)) + payload


EXE = os.environ.get('ADT_PROBE_EXE')


@unittest.skipUnless(EXE, 'set ADT_PROBE_EXE to run native x86 contracts')
class NativeProbeTests(unittest.TestCase):
    def setUp(self):
        self.exe = Path(EXE)

    def test_valid_return_and_reset_after_fault(self):
        probe = Probe(self.exe)
        fault = probe.call(cell(b'ZZZZ' + struct.pack('<I', 0xC1C1C1C1)))
        self.assertFalse(fault['returned'])
        self.assertEqual(fault['invalid'][0]['eip'], '0x7c3a42')
        self.assertTrue(fault['unknown'])
        self.assertTrue(fault['bounds'])
        good = probe.call(cell(b'TVCM\x04\0\0\0data'))
        self.assertTrue(good['returned'])
        for key in ('invalid', 'unknown', 'bounds', 'error', 'code_escape',
                    'instruction_limit_reached'):
            self.assertFalse(good[key], key)
        self.assertEqual(good['tag_visits'], 1)

    def test_return_does_not_hide_unknown_or_overrun(self):
        probe = Probe(self.exe)
        unknown = probe.call(cell(b'ZZZZ\0\0\0\0'))
        self.assertTrue(unknown['returned'])
        self.assertEqual(unknown['unknown'], [dict(offset=136, tag_hex='5a5a5a5a')])
        overrun = probe.call(cell(b'TVCM\x10\0\0\0'))
        self.assertTrue(overrun['returned'])
        self.assertFalse(overrun['invalid'])
        self.assertEqual([r['kind'] for r in overrun['bounds']], ['extent', 'final_cursor'])

    def test_instruction_budget_is_not_success(self):
        result = Probe(self.exe, instruction_limit=1).call(cell(b'TVCM\0\0\0\0'))
        self.assertFalse(result['returned'])
        self.assertTrue(result['instruction_limit_reached'])

    def test_function_hash_guard_rejects_modified_copy(self):
        raw = bytearray(self.exe.read_bytes())
        with pefile.PE(data=raw) as pe:
            offset = pe.get_offset_from_rva(START - pe.OPTIONAL_HEADER.ImageBase)
        raw[offset] ^= 1
        with tempfile.TemporaryDirectory() as tmp:
            modified = Path(tmp) / 'modified.exe'
            modified.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'function hash mismatch'):
                Probe(modified)


if __name__ == '__main__':
    unittest.main()
