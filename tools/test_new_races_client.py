#!/usr/bin/env python3
"""Offline regression tests against pinned local references; no client execution."""
import copy
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import unittest
import sys
import xml.etree.ElementTree as ET

import build_new_races_glue as glue
import patch_new_races_client as exe


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path('/home/dev/wow-335/Wow.exe')
        cls.raw = cls.source.read_bytes()
        cls.plan = json.loads(exe.PIN.read_text())
        cls.patched, cls.report = exe.patch_bytes(cls.raw)
        cls.sources, cls.turtle, cls.provenance = glue.load_sources(
            Path('/home/dev/wow-335'), Path('/home/dev/wow-turtle/Data/patch-9.mpq'), exe.ROOT / 'tools/mpq')
        cls.payload, cls.coords = glue.transform(cls.sources, cls.turtle)

    def test_authoritative_recipe_and_only_allowed_diffs(self):
        # The derivative's fixed digest independently pins the complete researched
        # recipe even when the ignored research directory is unavailable.
        proposal = exe.ROOT / 'work/new-races-client-research/cache-relocation-proposal.json'
        if proposal.exists():
            original = json.loads(proposal.read_text())
            for key in ('input_sha256', 'input_size', 'output_size', 'proposed_output_sha256', 'append'):
                self.assertEqual(self.plan[key], original[key])
            for a, b in zip(self.plan['edits'], original['edits'], strict=True):
                for key in ('file_offset', 'original', 'replacement'):
                    self.assertEqual(a[key], b[key])
        allowed = set()
        for edit in self.plan['edits']:
            start = int(edit['file_offset'], 0)
            old = bytes.fromhex(edit['original'])
            allowed.update(range(start, start+len(old)))
        self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(self.raw, self.patched))))
        self.assertEqual(self.patched[len(self.raw):], bytes(512))
        self.assertEqual(exe.sha(self.patched), exe.OUTPUT_SHA)
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_pe_cache_capacity_and_checksum(self):
        pe = exe.parse_pe(self.patched)
        section = pe['sections'][-1]
        self.assertEqual(section['virtual_size'], 24*2*4)
        self.assertEqual(section['characteristics'], 0xc0000040)
        self.assertEqual(section['characteristics'] & 0x20000000, 0)
        self.assertEqual(self.patched[0xe1034:0xe1038], struct.pack('<I', 0xc0))
        self.assertEqual(self.patched[0xe129b:0xe129f], struct.pack('<I', 24))
        refs = [e for e in self.plan['edits'] if e['original'] == 'd0 b0 b6 00']
        self.assertEqual(len(refs), 8)
        for ref in refs:
            off = int(ref['file_offset'], 0)
            self.assertEqual(struct.unpack_from('<I', self.patched, off)[0], 0xdfd000)
        self.assertEqual(exe.pe_checksum(self.patched, pe['checksum_offset']), pe['checksum'])
        # Known GlueXML validator call/switch remains byte-exact; cache fix does
        # not silently imply signature acceptance.
        self.assertEqual(self.raw[0xd9bdd:0xd9bf1], self.patched[0xd9bdd:0xd9bf1])

    def test_unknown_modified_and_idempotent_input_refusal(self):
        for data in (b'unknown', self.raw[:-1], self.patched, bytes([self.raw[0] ^ 1])+self.raw[1:]):
            with self.assertRaises(ValueError):
                exe.patch_bytes(data)
        plan = copy.deepcopy(self.plan)
        plan['edits'].pop(0)
        with self.assertRaisesRegex(ValueError, 'Eight old cache references'):
            exe.patch_bytes(self.raw, plan)
        plan = copy.deepcopy(self.plan)
        plan['edits'][0]['original'] = '00 00 00 00'
        with self.assertRaises(ValueError):
            exe.patch_bytes(self.raw, plan)

    def test_output_refusal_and_source_unchanged(self):
        for path in (self.source, self.source.parent / 'Other.exe', Path('/home/dev/wow-turtle/custom/Other.exe')):
            with self.assertRaises(ValueError):
                exe.safe_output(path, self.source)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / 'input' / 'Wow.exe'
            original.parent.mkdir()
            original.write_bytes(self.raw)
            output = root / 'derived' / 'Wow-new-races.exe'
            exe.build(original, output)
            self.assertEqual(original.read_bytes(), self.raw)
            self.assertEqual(output.read_bytes(), self.patched)
            with self.assertRaises(ValueError):
                exe.build(original, output)
            link = root / 'client-link'
            link.symlink_to(self.source.parent, target_is_directory=True)
            with self.assertRaises(ValueError):
                exe.safe_output(link / 'new.exe')

    def test_xml_layout_and_native_class_buttons(self):
        root = ET.fromstring(self.payload['Interface/GlueXML/CharacterCreate.xml'])
        native = ET.fromstring(self.sources['CharacterCreate.xml'])
        buttons = [e for e in root.iter(glue.NS+'CheckButton') if e.get('inherits') == 'CharacterCreateRaceButtonTemplate']
        self.assertEqual([int(b.get('id')) for b in buttons], list(range(1,13)))
        self.assertEqual(len({b.get('name') for b in buttons}), 12)
        columns = {-50: [], 50: []}
        for button in buttons:
            anchor = button.find(glue.NS+'Anchors/'+glue.NS+'Anchor')
            columns[int(anchor.get('x'))].append(int(anchor.get('y')))
        for rows in columns.values():
            self.assertEqual(len(rows), 6)
            self.assertTrue(all(a-b >= 38+12 for a,b in zip(rows, rows[1:])))
            self.assertLess(-rows[-1]+38, 388)  # last icon ends above native gender label
        def classes(tree):
            return [ET.tostring(e) for e in tree.iter(glue.NS+'CheckButton')
                    if e.get('inherits') == 'CharacterCreateClassButtonTemplate']
        self.assertEqual(len(classes(root)), 10)
        self.assertEqual(classes(root), classes(native))

    def test_stock_coords_and_native_api_paths_preserved(self):
        lua = self.payload['Interface/GlueXML/CharacterCreate.lua'].decode()
        native = self.sources['CharacterCreate.lua'].decode().replace('\r\n', '\n')
        for table in ('RACE_ICON_TCOORDS', 'CLASS_ICON_TCOORDS'):
            pattern = table + r' = \{.*?\n\};'
            self.assertEqual(re.search(pattern, lua, re.S)[0], re.search(pattern, native, re.S)[0])
        for anchor in ('select("#", ...)/3', 'SetSelectedRace(id)', 'IsRaceClassValid(CharacterCreate.selectedRace, index)',
                       'CharacterCreateEnumerateClasses(GetAvailableClasses())'):
            self.assertIn(anchor, lua)
        self.assertEqual(self.payload['Interface/Custom/NewRaces/RaceIcons.blp'], self.turtle['RaceIcons.blp'])
        self.assertEqual(self.coords['TURTLEGOBLIN_MALE'], [0.5, 0.625, 0, 0.25])
        self.assertEqual(glue.PICKER_IDS[5], 22)
        self.assertEqual(glue.PICKER_IDS[11], 23)

    def test_determinism_pins_and_payload_delivery(self):
        self.assertEqual(glue.transform(self.sources, self.turtle)[0], self.payload)
        bad = dict(self.sources, **{'CharacterCreate.lua': b'unknown'})
        with self.assertRaises(ValueError):
            glue.transform(bad, self.turtle)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            native, turtle = root/'native', root/'turtle'
            native.mkdir(); turtle.mkdir()
            for name, raw in self.sources.items(): (native/name).write_bytes(raw)
            for name, raw in self.turtle.items(): (turtle/name).write_bytes(raw)
            output = root/'generated'
            report = glue.build(output, source_dir=native, turtle_dir=turtle)
            for name, raw in self.payload.items():
                self.assertEqual((output/'payload'/name).read_bytes(), raw)
                self.assertEqual(report['payload'][name], exe.sha(raw))
            self.assertEqual(report['modified_GlueXML_acceptance'], 'NOT RUN')
            self.assertEqual(report['required_executable_sha256'], exe.CUSTOM_GLUE_SHA)
            with self.assertRaises(ValueError): glue.build(output, source_dir=native, turtle_dir=turtle)

    def test_actual_lua51_with_mocked_native_api(self):
        lua = os.environ.get('NEW_RACES_LUA') or shutil.which('lua5.1') or shutil.which('lua')
        if not lua:
            self.skipTest('Set NEW_RACES_LUA to a Lua 5.1 interpreter for mocked-API execution')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, raw in self.payload.items():
                dest = root/name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(raw)
            for locale in ('enUS', 'esES'):
                proc = subprocess.run([lua, str(glue.ASSETS/'test_native_glue.lua'), temp, locale], capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, proc.stdout+proc.stderr)
                self.assertIn('PASS mocked native glue', proc.stdout)

    def test_custom_gluexml_profile_only_changes_verified_entry_and_checksum(self):
        custom, report = exe.patch_bytes(self.raw, allow_custom_gluexml=True)
        self.assertEqual(exe.sha(custom), exe.CUSTOM_GLUE_SHA)
        self.assertEqual(report['profile'], 'cache-plus-custom-gluexml')
        self.assertEqual(report['modified_GlueXML_acceptance'], 'NOT RUN')
        diffs = {i for i,(a,b) in enumerate(zip(self.patched, custom)) if a != b}
        self.assertEqual(diffs, {0xd9dbc, 0x168})
        self.assertEqual(struct.unpack_from('<4I', self.raw, 0xd9db4),
                         (0x4da7f1, 0x4da7fe, 0x4da80b, 0x4da835))
        self.assertEqual(struct.unpack_from('<4I', custom, 0xd9db4),
                         (0x4da7f1, 0x4da7fe, 0x4da835, 0x4da835))
        pe = exe.parse_pe(custom)
        self.assertEqual(exe.pe_checksum(custom, pe['checksum_offset']), pe['checksum'])
        self.assertEqual(custom[0x4159e0:0x415b67], self.raw[0x4159e0:0x415b67])
        self.assertEqual(custom[0xd9c35:0xd9cf1], self.raw[0xd9c35:0xd9cf1])
        self.assertEqual(custom[0x129fd1:0x12a2c4], self.raw[0x129fd1:0x12a2c4])
        self.assertEqual(self.source.read_bytes(), self.raw)
        for patched in (custom, self.patched):
            with self.assertRaises(ValueError):
                exe.patch_bytes(patched, allow_custom_gluexml=True)

    def test_custom_gluexml_pin_guard_and_file_delivery(self):
        plan = copy.deepcopy(self.plan)
        plan['custom_gluexml_profile']['guards'][0]['bytes'] = '00'
        with self.assertRaisesRegex(ValueError, 'control-flow guard mismatch'):
            exe.patch_bytes(self.raw, plan, allow_custom_gluexml=True)
        plan = copy.deepcopy(self.plan)
        plan['custom_gluexml_profile']['edits_from_cache'][0]['replacement'] = 'fe a7 4d 00'
        with self.assertRaises(ValueError):
            exe.patch_bytes(self.raw, plan, allow_custom_gluexml=True)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)/'custom.exe'
            report = exe.build(self.source, output, allow_custom_gluexml=True)
            self.assertEqual(exe.sha(output.read_bytes()), exe.CUSTOM_GLUE_SHA)
            self.assertEqual(json.loads(output.with_suffix('.report.json').read_text()), report)
            self.assertEqual(report['gluexml_static_gate'],
                             'ALLOW status2 content digest mismatch; missing/invalid signature still rejected')

    def test_x86_gluexml_dispatch_and_postload_digest(self):
        # Optional independent execution of the *actual x86 basic blocks*, not
        # a Python reimplementation of their predicates. No Windows client run.
        if os.environ.get('NEW_RACES_UNICORN_PATH'):
            sys.path.insert(0, os.environ['NEW_RACES_UNICORN_PATH'])
        try:
            from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
            from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP, UC_X86_REG_ESP
        except ImportError:
            self.skipTest('Optional Unicorn x86 emulator unavailable; static branch tests still run')
        custom, _ = exe.patch_bytes(self.raw, allow_custom_gluexml=True)

        def execute(raw, start, stops, eax=0, same_digest=True):
            machine = Uc(UC_ARCH_X86, UC_MODE_32)
            machine.mem_map(0x400000, 0xa00000)
            # Text section: RVA0x1000, raw0x400, mapping delta0xc00.
            section = exe.parse_pe(raw)['sections'][0]
            machine.mem_write(0x400000+section['rva'],
                              raw[section['raw_offset']:section['raw_offset']+section['raw_size']])
            machine.mem_map(0x2000000, 0x10000)
            ebp = 0x2008000
            machine.reg_write(UC_X86_REG_EBP, ebp)
            machine.reg_write(UC_X86_REG_ESP, ebp-0x200)
            machine.reg_write(UC_X86_REG_EAX, eax)
            machine.reg_write(UC_X86_REG_EBX, 0)
            machine.mem_write(ebp-0x44, b'0123456789abcdef')
            machine.mem_write(ebp-0x54, b'0123456789abcdef' if same_digest else b'X123456789abcdef')
            reached = []
            def stop(uc, address, size, user):
                if address in stops:
                    reached.append(address)
                    uc.emu_stop()
            machine.hook_add(UC_HOOK_CODE, stop)
            machine.emu_start(start, 0, count=1000)
            self.assertEqual(len(reached), 1)
            return reached[0]

        stops = {0x4da7f1, 0x4da7fe, 0x4da80b, 0x4da835, 0x4da81e}
        for code, native_target in enumerate((0x4da7f1, 0x4da7fe, 0x4da80b, 0x4da835)):
            self.assertEqual(execute(self.raw, 0x4da7e5, stops, code), native_target)
            self.assertEqual(execute(custom, 0x4da7e5, stops, code),
                             0x4da835 if code == 2 else native_target)
        self.assertEqual(execute(custom, 0x4da7e5, stops, 4), 0x4da81e)
        self.assertEqual(execute(custom, 0x4da7e5, stops, 0xffffffff), 0x4da81e)
        for raw in (self.raw, custom):
            self.assertEqual(execute(raw, 0x4da863, {0x4da81e, 0x4da8f1}), 0x4da8f1)
            self.assertEqual(execute(raw, 0x4da863, {0x4da81e, 0x4da8f1}, same_digest=False), 0x4da81e)


if __name__ == '__main__':
    unittest.main(verbosity=2)
