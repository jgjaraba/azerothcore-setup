# Project custom world SQL

## Boundary and installation

This document records verified behavior of every SQL file in
`data/sql/custom/db_world/` as of the 2026-09-19 audit. The generated environment
inventory is authoritative for current filenames and working-tree state. These
are project-owned data overlays, not module migrations. `apply-db-world.sh`
lexically sorts and streams them to `acore_world`, stops at the first error, and
does not back up or make the batch atomic.

The observed lexical order is **not** a valid dependency order:
`forsaken_paladin_phase1_1.sql`, then `forsaken_paladin_phase1.sql`, then
`race_class_5_2.sql`. The trainer file runs last and deletes polished trainer
spawns, models, and equipment. Raid files likewise run `_item`, `_loot`, `_npc`,
then the defining `raid_gear_vendor.sql`. Locale can affect an unspecified sort
order. Do not use the installer as evidence that documented chains have been
applied correctly. Inspection `SELECT`s are observational, not validation gates.

All listed custom IDs, DBC records, and effective database state require
collision/availability checks; repository inspection cannot prove they exist in
a deployed database. The Transmog token customization is project-owned rather
than upstream module behavior; generated state records its current Git status.

## Feature chains

- **Forsaken Paladin:** `race_class_5_2.sql`, then
  `forsaken_paladin_phase1.sql`, then `forsaken_paladin_phase1_1.sql` (trainers,
  creation data, then trainer polish/spawns).
- **Individual Progression overlay:** `ground_riding_override.sql` and
  `remove_regular_mounts_ip_requisites.sql` after Individual Progression mount
  SQL/data.
- **Raid curios/vendors:** `raid_gear_vendor.sql`, `raid_gear_vendor_npc.sql`,
  `raid_gear_vendor_item.sql`, then `raid_gear_vendor_loot.sql` (definitions
  before inventory and loot use).
- **Independent changes:** `increase_world_boe_drop_rate.sql`,
  `rebalance_items.sql`, and `transmog_currency_loot.sql`; verify current
  core/module source data first.

## Per-file manifest

### `forsaken_paladin_phase1.sql`

- **Verified purpose/tables:** enables race `5`/class `2` creation with
  `playercreateinfo`, six `playercreateinfo_action` rows, and
  `charstartoutfit_dbc` IDs `9000`/`9001`.
- **Dependencies/assumptions:** current creation/outfit schemas, valid starting
  items/spells and Deathknell coordinates, and free outfit IDs. It is the base
  for the later food correction.
- **Rerun/update safety:** targeted delete/insert in a transaction is
  value-idempotent but destructive for those IDs; positional outfit inserts are
  schema-sensitive. Core/module data reloads can overwrite it.
- **Verification:** query exactly one creation row, six action rows, and two
  outfits; create an Undead Paladin and inspect location, abilities, gear, food,
  and water.

### `race_class_5_2.sql`

- **Verified purpose/tables:** clones source templates `2129`/`2123` into
  trainers `90210`/`90211` and writes `creature_template`, model/equipment,
  default trainer, and locale data. It first removes existing trainer spawns
  and addons; the later Paladin-polish file recreates them.
- **Dependencies/assumptions:** source templates, equipment source `23779`,
  trainer IDs `4`/`6`, unused custom entries, and matching schema/order for
  temporary-table `SELECT *` cloning.
- **Rerun/update safety:** deletes all data for both entries before recreation;
  absent sources can yield incomplete results after deletion. Re-running picks
  up source-template changes. Must precede Paladin polish.
- **Verification:** verify templates, trainer mappings, locales, models and
  equipment, then inspect trainer spell lists in game.

### `forsaken_paladin_phase1_1.sql`

- **Verified purpose/tables:** replaces starting food with `4604`, creates final
  trainer spawns `5300690`/`5300691`, custom model/equipment, and kneeling;
  touches outfits, `creature`, addon, model, and equipment tables.
- **Dependencies/assumptions:** both preceding Paladin files, item IDs
  `4604`/`1903`/`2813`/`6187`, free GUIDs, and current `bytes1` kneeling meaning.
- **Rerun/update safety:** largely delete/reinsert idempotent, but removes every
  spawn for entries `90210`/`90211`, not only known GUIDs. Its verification
  queries are outside its transaction.
- **Verification:** query final outfits/trainers/spawns/addons and inspect new
  character creation plus Deathknell/Brill trainer model, equipment, position,
  and animation.

### `ground_riding_override.sql`

- **Verified purpose/tables:** sets apprentice/journeyman riding spells
  `33388`/`33391` to levels 30/60 and changes matching ground mount
  `item_template` requirements.
- **Dependencies/assumptions:** Individual Progression
  `mounts_and_riding.sql`; item class/subclass/skill semantics and explicit
  item-speed lists remain current.
- **Rerun/update safety:** guarded absolute assignments are value-idempotent
  but not reversible. Broad metadata updates can affect future mounts; a module
  update can restore values. This file must run after the module's data.
- **Verification:** compare module/current mount lists and trainer spells;
  query targeted mounts and test 30/60 training and representative exceptions.

### `remove_regular_mounts_ip_requisites.sql`

- **Verified purpose/tables:** deletes Individual Progression WotLK conditions
  from mount items `46099`, `46100`, `46308`, and `47101` in `conditions`.
- **Dependencies/assumptions:** module mount SQL installed those exact
  condition-key dimensions and condition type `8`; correct selected database
  (the file has no `USE`).
- **Rerun/update safety:** transactional and deletion-idempotent, but could
  remove a future unrelated row with the same key. Must run after Individual
  Progression data and again after a module update that restores it.
- **Verification:** compare exact rows to current module SQL, query before/after,
  and inspect vendor visibility at relevant progression states.

### `raid_gear_vendor.sql`

- **Verified purpose/tables:** creates curio items `90002`–`90005` and locales
  by cloning item `29434`; affects `item_template` and `item_template_locale`.
- **Dependencies/assumptions:** source item, display IDs `21583`/`19502`/`34143`/
  `35350`, unused IDs, and current item schema compatible with `SELECT *`.
- **Rerun/update safety:** transactionally delete/recreates target items; absent
  source item leaves no recreated item while locale insertion still occurs.
  This is required before curio loot and should precede vendor inventory use.
- **Verification:** check source/display availability and final item flags,
  stack/bonding/locales; loot, stack, and vendor-sell each item in game.

### `raid_gear_vendor_npc.sql`

- **Verified purpose/tables:** creates Dark Rider vendors `90200`–`90203`, model
  data, localized templates/text/menu/options, and spawns `900000`–`900003`;
  affects creature, gossip, text, locale, and spawn tables.
- **Dependencies/assumptions:** client/server CreatureDisplayInfo `90100`,
  reserved entries/GUIDs/text IDs `92000`–`92003`, valid map coordinates, and
  vendor inventory supplied separately.
- **Rerun/update safety:** delete/reinsert is intended idempotence but commits
  three separate transactions, so partial install is possible. DBC/client patch
  mismatch can make functioning NPCs invisible.
- **Verification:** collision and DBC checks; query templates/flags/menus/spawns
  and vendor rows; verify rendering, Spanish text, gossip, and vendor UI.

### `raid_gear_vendor_item.sql`

- **Verified purpose/tables:** populates vendors `90200`–`90203` in `npc_vendor`
  with raid gear and ExtendedCost IDs `93010`–`96050`.
- **Dependencies/assumptions:** vendor entries, all item templates and
  client/server extended-cost records exist; entries are reserved for this
  catalog.
- **Rerun/update safety:** transactional full delete/reinsert is idempotent for
  this catalog but removes any other inventory on those entries. Static catalogs
  and costs can go stale.
- **Verification:** validate unique slots and all item/cost IDs, count rows by
  vendor, and attempt representative correct/incorrect-currency purchases.

### `raid_gear_vendor_loot.sql`

- **Verified purpose/tables:** gives curios guaranteed creature/chest drops and
  sets item flag `2048`; affects `item_template`, `creature_loot_template`, and
  `gameobject_loot_template`.
- **Dependencies/assumptions:** curio definitions, ordinary raid loot IDs, and
  Individual Progression Naxx40 entries `351000`–`351036`/chest `361000` with
  current loot references. Core source verifies flag `2048` enables individual
  `freeforall` loot behavior.
- **Rerun/update safety:** matching curio rows are replace-idempotent but absent
  targets are silently skipped. Module changes to Naxx data can invalidate it.
- **Open question:** comments claim currency-bag behavior, while item creation
  sets `BagFamily = 0`; multi-drop is verified but that extra claim is not.
- **Verification:** run missing-boss queries and exact loot/count checks, then
  group-test bosses and both special chests.

### `increase_world_boe_drop_rate.sql`

- **Verified purpose/tables:** multiplies selected Vanilla/TBC/WotLK green/blue/
  purple `reference_loot_template` chances by five (cap 100) from an embedded
  base-chance snapshot and temporary `_boe_base_chances` table.
- **Dependencies/assumptions:** MySQL temporary-table/`LEAST` support and the
  2,500-plus embedded tuples/comments still match current base data.
- **Rerun/update safety:** deterministic/value-idempotent from its snapshot,
  but intentionally overwrites matching current values and silently skips rows
  whose references/comments changed. Snapshot drift is the primary risk.
- **Verification:** compare every snapshot tuple/comment to current base SQL;
  query missing/mismatched rows and use a large-sample loot test only for
  statistical confirmation.

### `rebalance_items.sql`

- **Verified purpose/tables:** assigns `stat_type3 = 3`, `stat_value3 = 11` to
  item IDs `6975`–`6977` in `item_template`.
- **Dependencies/assumptions:** target rows exist and stat type `3` is still the
  intended stat. It has no module dependency.
- **Rerun/update safety:** absolute value assignments are idempotent but
  overwrite other item changes; no transaction or `USE` makes session/database
  selection an operational hazard.
- **Verification:** resolve current item names/stats, query all fields before/
  after, and inspect/equip in game if the change is player-visible.

### `transmog_currency_loot.sql`

- **Verified purpose/tables:** project-specific customization creates
  Transmogrification Mark `90001`, Spanish locale, and guaranteed selected
  level-60-era boss loot; affects `item_template`, locale, and creature loot.
- **Dependencies/assumptions:** reserved item ID; current boss templates with
  nonzero `lootid`; MySQL 8.0.19+ `INSERT ... AS ... ON DUPLICATE KEY UPDATE`;
  and
  Transmog runtime configuration explicitly consuming `90001` if it is intended
  as a charge. Core multi-drop behavior is verified for its item flag.
- **Rerun/update safety:** item/locale upserts and targeted loot replacement are
  idempotent, but missing boss/loot sources are silently skipped and current
  item/loot metadata is overwritten. It is integration data, not Transmog
  upstream behavior.
- **Portability:** row aliases after `VALUES` are documented MySQL 8.0.19+
  syntax and are not documented by MariaDB, which documents `VALUES(column)`
  instead. Treat MariaDB deployment as unsupported until exact-version testing
  proves otherwise.
- **Open question:** it targets normal Kel'Thuzad `15990`; Individual
  Progression Naxx40 uses custom `351019`. Intent for IP Naxx40 token rewards is
  unresolved.
- **Verification:** confirm MySQL syntax and entry-to-loot-ID mapping; query all
  drops and item flags/locales; group-test representative bosses and token use.

## Cross-cutting open issues and recommendations

- Establish a durable custom-ID/DBC registry for item `90001`–`90005`, creature
  `90200`–`90211`, display `90100`, text/menu IDs, GUIDs, and ExtendedCost IDs.
- Replace implicit lexical installation with an explicit post-module overlay
  order or manifest before treating the SQL batch as reproducible.
- Resolve the curio `BagFamily` contradiction and the Transmog token target/
  effective runtime-cost configuration with database and live-stack validation.
- Preserve non-secret deployment inputs for module SQL, DBC/client patches, and
  runtime settings; current custom world SQL alone cannot reconstruct them.

## Evidence

Each SQL file, relevant core loot/object code, current base schema, and relevant
Individual Progression/Transmog module source/data were inspected read-only on
2026-09-19. No database was queried or modified in this audit.
