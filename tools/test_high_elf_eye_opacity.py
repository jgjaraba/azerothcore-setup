"""Actual pinned M2/SKIN normalization and independent byte-field regressions."""
import json
import struct
import unittest

import consolidate_client_patches as c
from high_elf_eye_opacity import PINS, member, normalize_eye_opacity
from test_new_races_assets import validate_opacity_delta


class EyeOpacity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = c.Sources(json.loads(c.LOCK.read_text())).get(c.NEW)

    def inputs(self, sex):
        key = member(sex).lower()
        return self.source[key][1], self.source[key[:-3]+'00.skin'][1]

    def test_exact_native_values_and_idempotence_both_sexes(self):
        for sex in PINS:
            before, skin = self.inputs(sex)
            after, report = normalize_eye_opacity(before, skin, sex)
            validate_opacity_delta(before, after, sex)
            self.assertEqual(c.sha(after), PINS[sex][1])
            self.assertEqual(normalize_eye_opacity(after, skin, sex)[0], after)
            self.assertEqual(normalize_eye_opacity(after, skin, sex)[1]['changed_bytes'], 0)
            self.assertEqual(report['changed_bytes'], PINS[sex][4])

    def test_unknown_models_truncation_and_layout_fail_closed(self):
        for sex in PINS:
            model, skin = self.inputs(sex)
            for broken in (model[:-1], model+b'\0', b'XXXX'+model[4:]):
                with self.assertRaisesRegex(ValueError, 'Unknown.*model/layout'):
                    normalize_eye_opacity(broken, skin, sex)
            with self.assertRaises(ValueError):
                normalize_eye_opacity(model, skin[:-1], sex)
            broken = bytearray(skin)
            _, start = struct.unpack_from('<2I', skin, 36)
            # An unrelated batch must never share the eye-only weight combo.
            struct.pack_into('<H', broken, start+20, 1)
            with self.assertRaises(ValueError):
                normalize_eye_opacity(model, bytes(broken), sex)

    def test_independent_delta_rejects_geometry_times_track2_and_partial_opacity(self):
        for sex in PINS:
            before, skin = self.inputs(sex)
            after, report = normalize_eye_opacity(before, skin, sex)
            _, vertices = struct.unpack_from('<2I', before, 60)
            _, weights = struct.unpack_from('<2I', before, 88)
            _, time_descriptors = struct.unpack_from('<2I', before, weights+24)
            _, time_start = struct.unpack_from('<2I', before, time_descriptors)
            _, key_descriptors = struct.unpack_from('<2I', before, weights+52)
            _, track2_key = struct.unpack_from('<2I', before, key_descriptors)
            for p in (vertices, vertices+32, time_start, track2_key, report['key_offsets'][-1]):
                broken = bytearray(after); broken[p] ^= 1
                with self.assertRaises(ValueError):
                    validate_opacity_delta(before, bytes(broken), sex)


if __name__ == '__main__':
    unittest.main()
