#!/usr/bin/env python3
"""Merge Turtle pilot (KarazhanCrypt) rows into the 335 DBC set.

Adds:
  - Map.dbc:          map 800 KarazhanCrypt (dungeon)
  - AreaTable.dbc:    area 5086 Karazhan Crypt
Outputs merged DBCs to work/integrate/dbc/.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dbc_write import read_dbc_file, write_dbc_file, add_string

OUT = os.path.join(os.path.dirname(__file__), '..', 'work', 'integrate', 'dbc')
SRC = os.path.join(os.path.dirname(__file__), '..', 'work', 'extract', '335', 'dbc')

def merge_map():
    fc, records, sblk = read_dbc_file(os.path.join(SRC, 'Map.dbc'))
    assert fc == 66
    # build a new row for map 800
    sb = bytearray(sblk)
    def s(t):
        return add_string(sb, t)
    d = s('KarazhanCrypt')          # [1] internal name
    en = s('Karazhan Crypt')        # [5] enUS name
    es = s('Cripta de Karazhan')    # [11] esES name
    row = [0]*66
    row[0] = 800
    row[1] = d
    row[2] = 1          # MAP_INSTANCE (dungeon)
    row[3] = 0          # flags
    row[4] = 0
    row[5] = en
    row[11] = es        # esES at name[6]
    row[22] = 5086      # linked_zone
    row[57] = 0         # LoadingScreenID; refined to511 by build_crypt_loading.py
    row[58] = 1065353216  # BattlefieldMapIconScale = 1.0f
    row[59] = 0         # entrance_map (Deadwind Pass = map 0)
    row[60] = 0         # entrance_x
    row[61] = 0         # entrance_y
    row[62] = 0xFFFFFFFF
    row[63] = 0         # expansionID (vanilla)
    row[64] = 0
    row[65] = 5         # maxPlayers
    records.append(row)
    records.sort(key=lambda r: r[0])
    write_dbc_file(os.path.join(OUT, 'Map.dbc'), fc, records, bytes(sb))
    print(f'Map.dbc: added 800, total {len(records)}')

def merge_areatable():
    fc, records, sblk = read_dbc_file(os.path.join(SRC, 'AreaTable.dbc'))
    assert fc == 36
    sb = bytearray(sblk)
    def s(t):
        return add_string(sb, t)
    en = s('Karazhan Crypt')
    es = s('Cripta de Karazhan')
    row = [0]*36
    row[0] = 5086
    row[1] = 800        # mapid
    row[2] = 0          # zone (0 = it's a zone)
    row[3] = 0          # exploreFlag
    row[4] = 0          # flags
    row[10] = 60        # area_level
    row[11] = en        # enUS name
    row[17] = es        # esES name (area_name[6] = field 11+6)
    row[28] = 0         # team
    # 29-32 liquid type override = 0
    records.append(row)
    records.sort(key=lambda r: r[0])
    write_dbc_file(os.path.join(OUT, 'AreaTable.dbc'), fc, records, bytes(sb))
    print(f'AreaTable.dbc: added 5086, total {len(records)}')

def merge_mapdifficulty():
    fc, records, sblk = read_dbc_file(os.path.join(SRC, 'MapDifficulty.dbc'))
    assert fc == 23
    # 754 and 755 are SQL overlays for the project's Naxx40/Onyxia content.
    # Checked against DEV mapdifficulty_dbc as well as the input DBC.
    difficulty_id = 756
    if any(r[0] == difficulty_id or r[1] == 800 for r in records):
        raise ValueError('Pilot MapDifficulty ID/map already exists in the input DBC')
    row = [0]*23
    row[0] = difficulty_id
    row[1] = 800        # MapId
    row[2] = 0          # Difficulty (normal)
    row[19] = 16712188  # textFlags (same as vanilla 5-man Gnomeregan)
    row[20] = 0         # resetTime
    row[21] = 5         # maxPlayers
    records.append(row)
    records.sort(key=lambda r: r[0])
    write_dbc_file(os.path.join(OUT, 'MapDifficulty.dbc'), fc, records, sblk)
    print(f'MapDifficulty.dbc: added map 800, total {len(records)}')

def main():
    os.makedirs(OUT, exist_ok=True)
    merge_map()
    merge_areatable()
    merge_mapdifficulty()

if __name__ == '__main__':
    main()
