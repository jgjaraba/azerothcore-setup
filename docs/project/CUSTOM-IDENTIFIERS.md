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

The ExtendedCost values remain a set rather than an asserted contiguous
allocation: the vendor catalog consumes specific IDs and repository inspection
does not establish their project ownership.

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
