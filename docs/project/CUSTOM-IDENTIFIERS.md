# Custom identifier registry

## Purpose and evidence rule

This registry records project identifiers evidenced by tracked project assets
or required project integrations. It is not a global namespace reservation and
does not infer ownership from a numeric value. `Observed in DEV` means a
read-only check found the specified current row(s) on 2026-09-20; it is not a
uniqueness proof outside the checked table or a deployment history.

New allocations require collision checks against relevant tracked core/module
SQL, current DEV tables, and server/client DBC where applicable. “Unused in one
query” is not a reservation. Record retired identifiers rather than silently
reusing them. A durable range-allocation policy remains undecided.

## Project feature identifiers

- **Item templates `90001`–`90005`:** `90001` is the Transmogrification Mark;
  `90002`–`90005` are raid curios. Defined by
  `transmog_currency_loot.sql` and `raid_gear_vendor.sql`. All five rows were
  observed in DEV; wider ownership is unverified.
- **Creature templates `90200`–`90203`:** Dark Rider raid vendors, defined by
  `raid_gear_vendor_npc.sql`; observed in DEV. Wider ownership is unverified.
- **Creature templates `90210`, `90211`:** Forsaken Paladin trainers, defined
  by `forsaken_paladin.sql`; observed in DEV. Wider ownership is unverified.
- **Creature spawn GUIDs `900000`–`900003`:** Dark Rider vendor spawns, defined
  by `raid_gear_vendor_npc.sql`; four rows observed in DEV. Global GUID
  collision is not proven.
- **Creature display `90100`:** Dark Rider display dependency referenced by
  `raid_gear_vendor_npc.sql`. Server/client DBC availability is unverified.
- **Gossip/text/menu `92000`–`92003`:** Dark Rider dialogue/menu dependencies
  referenced by `raid_gear_vendor_npc.sql`. Table-level collision was not
  checked.
- **ExtendedCost values used by the raid vendor catalog:** `93010`, `93050`,
  `93100`, `94005`, `94010`, `95010`, `95050`, `96005`, `96010`, and `96050`.
  Referenced by `raid_gear_vendor_item.sql` and observed in the DEV vendor rows;
  DBC availability and ownership/uniqueness are unverified.
- **Item templates `91001`–`91079`:** MorphSummon appearance-unlock items in
  the project module fork. All templates and requirement rows were observed in
  DEV; the full client-data contract is unverified.
- **Quest templates `91010`–`91016`, `91020`–`91024`:** Forsaken Paladin
  Redemption and weapon-chain quests, defined by `forsaken_paladin_quests.sql`.
  These are quest IDs, not item-template IDs: their numeric overlap with the
  MorphSummon item namespace `91001`–`91079` is intentional and safe because
  the database tables and client records are distinct.
- **Item templates and Item.dbc records `92060`–`92064`:** Forsaken Paladin
  weapon-chain components and Lordaeron's Vigil, defined by
  `forsaken_paladin_quests.sql` and mapped by
  `dbc/forsaken_paladin_item_dbc_mapping.csv`. Observed in DEV. Their server
  Item.dbc and both client patch-Z variants must retain existing custom records
  and include these five IDs.
- **`charstartoutfit_dbc` records `9002`–`9015`:** Orc Mage (`9002`/`9003`),
  Troll Warlock (`9004`/`9005`), Blood Elf Warrior (`9006`/`9007`), Night Elf
  Mage (`9008`/`9009`), Draenei Rogue (`9010`/`9011`), Tauren Priest
  (`9012`/`9013`), and Gnome Hunter (`9014`/`9015`) start-outfit overlays.
  Defined by `orc_mage_troll_warlock.sql` and `cata_race_class_combos.sql`.
  Project-owned IDs; collision-checked against the current maximum
  `charstartoutfit_dbc.ID`.
- **`skillraceclassinfo_dbc` records `200000`–`200001`:** Gnome Hunter weapon
  skill availability (Guns `46` and Axes `44`). Defined by
  `cata_race_class_combos.sql`; collision-checked against the empty
  `skillraceclassinfo_dbc` table.

The ExtendedCost values remain a set rather than an asserted contiguous
allocation: the vendor catalog consumes specific IDs and repository inspection
does not establish their project ownership.

## Karazhan Crypt geographic and native-access pilot

Project manifest: `tools/crypt_portals.json`; SQL:
`data/sql/custom/db_world/turtle_wow_crypt_access.sql`.

| Namespace | Allocated IDs | Contract |
|---|---|---|
| Map.dbc | `800` | independent `KarazhanCrypt` dungeon |
| AreaTable.dbc | `5086` | pilot zone on map800 |
| MapDifficulty.dbc | `756` | map800 / normal0;754 and755 are existing SQL overlays |
| WorldMapArea.dbc | `674` | map800 / area5086; preserve independent client/server baselines |
| LoadingScreens.dbc | `511` | Turtle loading art;335 Map field57 references it |
| AreaTrigger.dbc / SQL shape / teleport | `900800`, `900801` | map0 entrance / map800 exit |
| Gameobject template entries | `900800`, `900801` | decorative native display672, type5, scale1.6 |
| Gameobject spawn GUIDs | `900800`, `900801` | one phase1/normal spawn per portal |
| Dungeon access template | `124` | map800, difficulty0, min55; no quest/key requirements |

Allocated in project source; deployment is not implied. Read-only collision
checks on 2026-10-20 found the nine target DEV rows absent, no related trigger
bindings/access requirements, and no competing source references in project data
or core/module SQL/C++ sources. Client/server baseline AreaTrigger IDs were
checked independently; the builder repeats these checks (identical owned DEV
rows are accepted on reruns). WotLK trigger `5008` belongs to Nagrand Arena and
is preserved; Turtle `5008`/`5011` are provenance only, not imported identifiers.
See [`../turtle-wow/id-mappings.md`](../turtle-wow/id-mappings.md) for all pilot
namespace bindings and collision lessons, and `../turtle-wow/crypt-portals.md`
for placement/access contracts. Other regions are not assigned IDs merely by
listing their Turtle source identifiers.

## External/module dependencies, not project allocations

- **Creature templates `390011`, `190012`, and `601072`:** Character Services,
  Reagent Bank Account, and base MorphSummon NPCs respectively. Module SQL owns
  them; one DEV row for each was observed.
- **Quest templates `66001`–`66018` currently:** Individual Progression hidden
  progression state. Module source uses the `66000 + state` convention; 18 DEV
  rows were observed. This is not a project-owned allocation.
- **Individual Progression Naxx40 creature/gameobject entries:** a raid-curio
  loot prerequisite. Project SQL consumes selected module entries; ownership and
  collision checks remain in module data.

## Client/server contract

`90001`–`90005`, `92060`–`92064`, display `90100`, and the raid vendor
ExtendedCost values can cross the database/server-DBC/client-patch boundary.
Tracked DBC and MPQ files exist, but their deployed hashes, regular/HD parity,
and complete record availability are UNKNOWN. Consult `components/client-assets.md`
before changing one side of these contracts.
