#!/usr/bin/env python3
"""Offline data-contract/geometry tests. Never applies SQL or changes inputs."""
import math
import struct
import unittest

from build_crypt_portals import (ROOT, SQL, contains, equal, generate_sql, load_manifest,
                                 merge_dbc, parse_dbc, sql_rows, client_map_rows)


class CryptPortalsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load_manifest()
        cls.entry, cls.exit = cls.m['portals']

    def test_oriented_box_reachable_before_wall(self):
        t = self.entry['trigger']
        _, x, y, z, _, length, width, height, o = t
        corners = [(x+u*math.cos(o)-v*math.sin(o), y+u*math.sin(o)+v*math.cos(o))
                   for u in (-length/2, length/2) for v in (-width/2, width/2)]
        wall_y_min = self.m['provenance']['native_barrier_world_aabb'][1][0]
        self.assertLess(max(c[1] for c in corners), wall_y_min - 0.4)
        self.assertTrue(contains(t, [0, -11068.14, -1826.3, 60.2]))
        # Thin axis faces the wall; the broad axis crosses the passage.
        for local_x, local_y, expected in ((0.49, 3.99, True), (0.51, 0, False),
                                            (0, 4.01, False)):
            point = [0, x+local_x*math.cos(o)-local_y*math.sin(o),
                     y+local_x*math.sin(o)+local_y*math.cos(o), z]
            self.assertEqual(contains(t, point), expected)
        self.assertFalse(contains(t, [0, x, y, z+height/2+0.01]))
        self.assertFalse(contains(t, [800, x, y, z]))
        self.assertFalse(contains(t, [0, -11068.14, -1825.0, 60.2]))

    def test_arrivals_do_not_bounce_and_clear_floors(self):
        # Client and this non-tavern handler use strict volumes (delta=0).
        # Also check a hypothetical 1.5-yard expansion conservatively; this
        # extra margin is a test condition, not the server's actual behavior.
        for portal, opposing in ((self.entry, self.exit), (self.exit, self.entry)):
            arrival = portal['destination'][:4]
            self.assertEqual(arrival[0], opposing['trigger'][0])
            self.assertFalse(contains(opposing['trigger'], arrival))
            self.assertFalse(contains(opposing['trigger'], arrival, delta=1.5))
        for field in ('arrival_z', 'return_z'):
            z = self.m['provenance'][field]
            self.assertGreater(z['adapted'], z['floor'])
            self.assertLess(z['adapted']-z['floor'], 0.2)
        self.assertEqual(self.exit['trigger'], self.m['provenance']['turtle_exit'][1:])

    def test_stable_insertion_preserves_native_bits_and_relative_order(self):
        # Deliberately include bytes that are float NaNs if misinterpreted;
        # native rows must be copied, never converted/re-serialized.
        native = [struct.pack('<10I', i, 0, 0x7fc01234, 0xffffffff, *([0]*6))
                  for i in range(1, 1218)]
        nagrand = struct.pack('<2I8f', 5008, 559, 4054.15, 2923.7, -20, 0, 214, 216, 20, .468)
        native += [nagrand, struct.pack('<2I8f', 5340, 571, *([0]*8)),
                   struct.pack('<2I8f', 5001, 578, *([0]*8))]
        strings = b'\0native\0\xff\x80preserve\0'
        raw = struct.pack('<4s4I', b'WDBC', 1220, 10, 40, len(strings)) + b''.join(native) + strings
        merged = merge_dbc(raw, self.m)
        owned = {p['id'] for p in self.m['portals']}
        self.assertEqual([merged[20+i*40:60+i*40] for i in range(1222)
                          if struct.unpack_from('<I', merged, 20+i*40)[0] not in owned], native)
        self.assertEqual(merged[-len(strings):], strings)
        rows, _ = parse_dbc(merged)
        lookup = {r[0]: r for r in rows}
        self.assertEqual(lookup[5008][1], 559)
        self.assertEqual(len(rows), 1222)
        for p in self.m['portals']:
            expected = struct.pack('<2I8f', p['id'], *p['trigger'])
            index = next(i for i, r in enumerate(rows) if r[0] == p['id'])
            self.assertEqual(merged[20+40*index:60+40*index], expected)
            self.assertGreater(p['id'], 65535)  # IDs are uint32, not uint16.

    def test_client_scan_reproduces_append_bug_and_finds_sorted_portals(self):
        native = [struct.pack('<2I8f', i+1, 0 if i < 175 else 724, *([0]*8))
                  for i in range(1220)]
        raw = struct.pack('<4s4I', b'WDBC', 1220, 10, 40, 1) + b''.join(native) + b'\0'
        legacy = (struct.pack('<4s4I', b'WDBC', 1222, 10, 40, 1) + b''.join(native)
                  + b''.join(struct.pack('<2I8f', p['id'], *p['trigger']) for p in self.m['portals'])
                  + b'\0')
        self.assertNotIn(900800, {r[0] for r in client_map_rows(parse_dbc(legacy)[0], 0)})
        fixed = parse_dbc(merge_dbc(raw, self.m))[0]
        self.assertEqual([r[1] for r in fixed], sorted(r[1] for r in fixed))
        self.assertIn(900800, {r[0] for r in client_map_rows(fixed, 0)})
        self.assertIn(900801, {r[0] for r in client_map_rows(fixed, 800)})
        self.assertEqual(fixed[175][0], 900800)

    def test_truncated_duplicate_and_collision_dbc_rejected(self):
        row = struct.pack('<2I8f', 900800, 0, *([0]*8))
        raw = struct.pack('<4s4I', b'WDBC', 1220, 10, 40, 1) + b''.join(
            struct.pack('<2I8f', i, 0, *([0]*8)) for i in range(1, 1220)) + row + b'\0'
        with self.assertRaisesRegex(ValueError, 'collision'):
            merge_dbc(raw, self.m)
        with self.assertRaises(ValueError):
            parse_dbc(raw[:-1])
        duplicate = raw[:20] + row*1220 + b'\0'
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            parse_dbc(duplicate)

    def test_manifest_sql_and_visual_contract(self):
        sql = generate_sql(self.m)
        self.assertEqual(SQL.read_text(), sql)
        self.assertEqual(sql.count('INSERT INTO '), 9)
        self.assertEqual(sql.count('WHERE NOT EXISTS (SELECT 1 FROM '), 9)
        self.assertNotRegex(sql.upper(), r'\b(DELETE|IGNORE|REPLACE|UPDATE)\b')
        self.assertIn('DECLARE EXIT HANDLER FOR SQLEXCEPTION', sql)
        self.assertIn('ROLLBACK;\n    RESIGNAL;', sql)
        self.assertNotIn('INSERT INTO `instance_template`', sql)
        for table, row in sql_rows(self.m):
            if table == 'gameobject':
                self.assertEqual((row['phaseMask'], row['spawnMask'], row['state']), (1, 1, 1))
                self.assertAlmostEqual(row['rotation2']**2 + row['rotation3']**2, 1)
                self.assertAlmostEqual(row['rotation2'], math.sin(row['orientation']/2))
            elif table == 'gameobject_template':
                self.assertEqual((row['type'], row['displayId'], row['Data1'], row['Data6']), (5, 672, 1, -1))
                self.assertEqual((row['AIName'], row['ScriptName']), ('', ''))
                self.assertEqual([row[f'Data{i}'] for i in range(24) if i not in (1, 6)], [0]*22)
        manifest = (ROOT / 'data/sql/custom/db_world/manifest.txt').read_text().splitlines()
        self.assertEqual(manifest[-2:], ['turtle_wow_maps.sql', SQL.name])
        prerequisite = (SQL.parent / 'turtle_wow_maps.sql').read_text()
        self.assertNotRegex(prerequisite.upper(), r'\b(DELETE|IGNORE|REPLACE|UPDATE)\b')
        self.assertIn('WHERE NOT EXISTS', prerequisite)
        self.assertIn("BINARY `script` = BINARY ''", prerequisite)

    def test_near_zero_radius_is_a_conflicting_sphere(self):
        # A universal 1e-3 identity tolerance would accept this incompatible
        # shape, even though its activation behavior differs completely.
        box = self.entry['trigger']
        sphere = list(box)
        sphere[4] = 0.0005
        portal_ground = [0, -11068.14, -1826.3, 60.2]
        self.assertTrue(contains(box, portal_ground))
        self.assertFalse(contains(sphere, portal_ground))
        self.assertEqual(equal('radius', 0), '`radius` <=> 0')
        self.assertIn('AND `radius` <=> 0', SQL.read_text())


if __name__ == '__main__':
    unittest.main()
