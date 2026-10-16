# Orc Mage and Troll Warlock

Status: implemented. Server-side data validated by DB application and
worldserver startup; client patch-Z already contains the required DBC rows.
In-game acceptance tests (character creation, spawn, quest chains) remain human
steps.

## Design contract

- Enable two additional playable race/class combinations in the 3.3.5a client
  and server:
  - **Orc Mage** — race 2, class 8.
  - **Troll Warlock** — race 8, class 9.
- Both combinations behave as the underlying race and class: Orc/Troll start
  positions, racial abilities, class spells/skills, and stats.
- No new quests or quest IDs are created. Existing race-specific class quests
  are extended to the new race by updating only the `AllowableRaces` bitmask.
- Existing combinations, custom DBC rows, and existing custom SQL must not be
  altered or removed.

## Ownership

- `data/sql/custom/db_world/orc_mage_troll_warlock.sql` is the sole canonical
  owner of the server-side creation data and quest race-mask extensions.
- It is listed in `data/sql/custom/db_world/manifest.txt` immediately after the
  Forsaken Paladin files.
- The tracked client patch-Z archives (`client_patches/regular_client/patch-Z.mpq`
  and `client_patches/hd_client/patch-Z.mpq`) already contain the required
  `DBFilesClient\CharBaseInfo.dbc` and `DBFilesClient\CharStartOutfit.dbc`
  records for both combinations. No new client DBC work was required for this
  task.

## Implementation

### Client data

The project patch-Z files contain a 72-record `CharBaseInfo.dbc` and a
200-record `CharStartOutfit.dbc`. Both already include:

- `CharBaseInfo`: `(2, 8)` Orc Mage and `(8, 9)` Troll Warlock.
- `CharStartOutfit`: rows `35`/`36` for Orc Mage and `157`/`158` for Troll
  Warlock.

Existing custom records — including the Forsaken Paladin outfits and all custom
Item/ExtendedCost/CreatureDisplayInfo entries — were preserved; no records were
removed or regenerated.

### Server data

The server DBC file used by the DEV install is the original 126-record
`CharStartOutfit.dbc` and lacks the new combo rows. The SQL therefore supplies
the outfits through the standard `charstartoutfit_dbc` DB overlay mechanism.

The SQL creates:

| Table | Rows | Purpose |
|---|---|---|
| `playercreateinfo` | `(2, 8)`, `(8, 9)` | Valley of Trials spawn: map 1, zone 14, position `(-618.518, -4251.67, 38.718, 0)` |
| `playercreateinfo_action` | `(2, 8)`, `(8, 9)` | Attack, first class spell, racial, food/water |
| `charstartoutfit_dbc` | `9002`/`9003`, `9004`/`9005` | Start outfits cloned from existing Troll Mage / Orc Warlock rows |

Outfit IDs were chosen after confirming the current maximum
`charstartoutfit_dbc.ID` was `9001`.

The start outfits are cloned field-for-field from the existing source rows:

| New ID | Race | Class | Sex | Cloned from |
|---|---|---|---|---|
| `9002` | 2 (Orc) | 8 (Mage) | 0 | Troll Mage `317` |
| `9003` | 2 (Orc) | 8 (Mage) | 1 | Troll Mage `318` |
| `9004` | 8 (Troll) | 9 (Warlock) | 0 | Orc Warlock `20` |
| `9005` | 8 (Troll) | 9 (Warlock) | 1 | Orc Warlock `46` |

Class skills, languages, and level stats are already covered by the existing
`playercreateinfo_skills`, `player_race_stats`, and `player_class_stats` data
for these races/classes, so no additional rows were needed.

### Quest extensions

No quest content was duplicated and no new `quest_template` IDs were created.
Race masks were extended with a guarded bitwise OR so the change is idempotent
and preserves the original race access.

| Quest ID | Title | Original race | New race | Class kept |
|---|---|---|---|---|
| `3086` | Glyphic Tablet | Troll (`128`) | Orc (`2`) | Mage (`128`) |
| `3090` | Tainted Parchment | Orc (`2`) | Troll (`128`) | Warlock (`256`) |
| `1506` | Gan'rul's Summons | Orc (`2`) | Troll (`128`) | Warlock (`256`) |
| `1501` | Creature of the Void | Orc (`2`) | Troll (`128`) | Warlock (`256`) |
| `1504` | The Binding | Orc (`2`) | Troll (`128`) | Warlock (`256`) |
| `10790` | Return to Gan'rul Bloodeye | Orc (`2`) | Troll (`128`) | Warlock (`256`) |

Resulting race mask for all six quests: `130` (`2 | 128`).

Prerequisites, quest starters/enders, conditions, and items were inspected and
left unchanged because none impose an additional race restriction.

## Validation

- `scripts/apply-db-world.sh --validate` passes.
- The full manifest applies successfully twice (idempotency check).
- DB queries confirm the new `playercreateinfo`, `playercreateinfo_action`, and
  `charstartoutfit_dbc` rows and the updated quest race masks.
- `worldserver` starts and loads Player Create data without errors related to
  the new rows.
- Existing Troll Mage (`8, 8`) and Orc Warlock (`2, 9`) creation data was not
  modified.

## Maintenance considerations

- If the project ever updates the server `CharStartOutfit.dbc` to the tracked
  200-record client version, the `charstartoutfit_dbc` overlay rows remain
  harmless because the loader resolves by `(race, class, gender)` and the DB
  rows match the same key.
- Future custom race/class combinations should reuse this pattern: add
  `playercreateinfo`, `playercreateinfo_action`, and `charstartoutfit_dbc`
  overlay rows, and extend existing race-specific quests only via race-mask
  updates.
- Any change to the Troll Mage or Orc Warlock start outfits must be mirrored
  onto rows `9002`–`9005` to keep the cloned outfits consistent.
