# Cataclysm race/class combos

Status: implemented. Server-side data validated by DB application and
worldserver startup (`Loaded 70 Player Create Definitions`). In-game acceptance
tests (character creation, spawn, quest chains) remain human steps.

## Design contract

Enable five additional playable race/class combinations that the tracked client
`CharBaseInfo.dbc` already exposes but the base AzerothCore DB does not support:

| Race | Class | IDs |
|---|---|---|
| Blood Elf | Warrior | `10` / `1` |
| Night Elf | Mage | `4` / `8` |
| Draenei | Rogue | `11` / `4` |
| Tauren | Priest | `6` / `5` |
| Gnome | Hunter | `7` / `3` |

Each combination uses the underlying race's normal starting area, racial
abilities, class spells/skills, and stats. No new quests or quest IDs are
created; existing race-specific class quests are extended only by updating
`AllowableRaces` with a guarded bitwise OR.

## Ownership

- `data/sql/custom/db_world/cata_race_class_combos.sql` is the sole canonical
  owner of the server-side creation data and the Gnome/Dwarf Hunter quest
  race-mask extension.
- It is listed in `data/sql/custom/db_world/manifest.txt` after
  `soul_shard_stacks.sql`.
- The tracked client patch-Z archives already contain the required
  `DBFilesClient\CharBaseInfo.dbc` rows; no new client DBC work was required.

## Implementation

### Server data

The base server `CharStartOutfit.dbc` lacks start outfits for these
combinations, so the SQL supplies them through the `charstartoutfit_dbc` DB
overlay mechanism. The overlay values are taken directly from the tracked
client `dbc/CharStartOutfit.dbc` (200-record Cataclysm file), not from the
base server's smaller DBC import.

The SQL creates:

| Table | Rows | Purpose |
|---|---|---|
| `playercreateinfo` | `(10,1)`, `(4,8)`, `(11,4)`, `(6,5)`, `(7,3)` | Standard race start positions |
| `playercreateinfo_action` | same combos | Attack, first class spells, racial, food/water |
| `charstartoutfit_dbc` | `9006`–`9015` | Start outfits from client DBC |
| `playercreateinfo_skills` | 5 rows | Starting weapon proficiencies for the new combos |
| `skillraceclassinfo_dbc` | `200000`–`200001` | Allows Gnome Hunters to learn Guns/Axes |

Outfit IDs were chosen after confirming the current maximum
`charstartoutfit_dbc.ID` was `9005`. SkillRaceClassInfo IDs were chosen after
confirming the `skillraceclassinfo_dbc` table was empty.

| New ID | Race | Class | Sex | Source DBC ID | Notes |
|---|---|---|---|---|---|
| `9006` | 10 (Blood Elf) | 1 (Warrior) | 0 | `161` | Uses Blood Elf Warrior start gear |
| `9007` | 10 (Blood Elf) | 1 (Warrior) | 1 | `162` | Uses Blood Elf Warrior start gear |
| `9008` | 4 (Night Elf) | 8 (Mage) | 0 | `75` | Uses Night Elf Mage start gear |
| `9009` | 4 (Night Elf) | 8 (Mage) | 1 | `76` | Uses Night Elf Mage start gear |
| `9010` | 11 (Draenei) | 4 (Rogue) | 0 | `187` | Uses Draenei Rogue start gear |
| `9011` | 11 (Draenei) | 4 (Rogue) | 1 | `188` | Uses Draenei Rogue start gear |
| `9012` | 6 (Tauren) | 5 (Priest) | 0 | `109` | Uses Tauren Priest start gear |
| `9013` | 6 (Tauren) | 5 (Priest) | 1 | `110` | Uses Tauren Priest start gear |
| `9014` | 7 (Gnome) | 3 (Hunter) | 0 | `125` | Uses Gnome Hunter start gear |
| `9015` | 7 (Gnome) | 3 (Hunter) | 1 | `126` | Uses Gnome Hunter start gear |

Class skills, languages, and level stats are already covered by the existing
`playercreateinfo_skills`, `player_race_stats`, and `player_class_stats` data
for these races/classes, but the starting weapon skills are not. The SQL adds
`playercreateinfo_skills` rows for the weapons each new combo starts with, and
`skillraceclassinfo_dbc` rows so Gnome Hunters can learn Guns (`46`) and Axes
(`44`).

### Quest extensions

No quest content was duplicated and no new `quest_template` IDs were created.
Race masks were extended with a guarded bitwise OR.

| Quest ID | Title | Original race | Added race | Class kept |
|---|---|---|---|---|
| `3108` | Etched Rune | Dwarf (`4`) | Gnome (`64`) | Hunter (`4`) |
| `6074` | The Hunter's Path | Dwarf (`4`) | Gnome (`64`) | Hunter (`4`) |
| `6075` | The Hunter's Path | Dwarf (`4`) | Gnome (`64`) | Hunter (`4`) |
| `6076` | The Hunter's Path | Dwarf (`4`) | Gnome (`64`) | Hunter (`4`) |
| `6064` | Taming the Beast | Dwarf (`4`) | Gnome (`64`) | Hunter (`4`) |
| `6084` | Taming the Beast | Dwarf (`4`) | Gnome (`64`) | Hunter (`4`) |
| `6085` | Taming the Beast | Dwarf (`4`) | Gnome (`64`) | Hunter (`4`) |
| `6086` | Training the Beast | Dwarf (`4`) | Gnome (`64`) | Hunter (`4`) |

Resulting race mask for all eight quests: `68` (`4 | 64`).

Prerequisites, quest starters/enders, conditions, and items were inspected and
left unchanged because none impose an additional race restriction.

## Validation

- `scripts/apply-db-world.sh --validate` passes.
- The full manifest applies successfully twice (idempotency check).
- DB queries confirm the new `playercreateinfo`, `playercreateinfo_action`,
  `charstartoutfit_dbc`, `playercreateinfo_skills`, and `skillraceclassinfo_dbc`
  rows and the updated quest race masks.
- `worldserver` starts and loads `70 Player Create Definitions` without errors
  related to the new rows.
- Existing source outfit rows were not modified.

## Maintenance considerations

- The `charstartoutfit_dbc` overlay rows were generated from
  `dbc/CharStartOutfit.dbc` using the Cata DBC layout: the first field is a
  packed `RaceID|ClassID|SexID|OutfitID`, item IDs start at field index 2,
  display IDs at field index 26, and inventory types at field index 50.
  Re-extracting from a newer client DBC should follow the same mapping.
- Future custom race/class combinations should reuse this pattern: add
  `playercreateinfo`, `playercreateinfo_action`, and `charstartoutfit_dbc`
  overlay rows, and extend existing race-specific quests only via race-mask
  updates.
- Any change to the source outfits must be regenerated from the client DBC and
  mirrored onto the overlay rows to keep them consistent.
