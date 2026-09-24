# Custom content and ID namespace inventory

**Collection date:** 2026-09-24. This is an evidence inventory, not a global ID
reservation. The reviewed allocation claims are in
[`custom-content-registry.csv`](custom-content-registry.csv); run
`scripts/agent/inventory-custom-content.sh` to regenerate DEV observations.

## Executive summary

- **Project-owned:** 5 item templates, 6 creature templates, 4 creature spawns,
  4 NPC-text/gossip menus/options, and one unverified display dependency.
- **Module-owned:** 79 MorphSummon items; 18 Individual Progression quests; 93
  Naxx40 creature templates; 2 Naxx40 gameobjects; and module NPC/DBC records
  listed in the registry.
- **Canonical overrides:** riding/mount requirements, BoE loot chances, three
  existing item stats (`6975`–`6977`), and selected module loot conditions are
  project SQL changes, not new allocations.
- **No verified same-namespace collision** was found for the project allocations.
  Equal numbers in different namespaces are legal: Individual Progression spell
  `90001` is not the project item `90001`.

## Verified project allocations

| Namespace | Occupied keys | Owner / source | DEV |
|---|---|---|---|
| `item_template` | `90001`–`90005` | project Transmog/Raid Curios SQL | PRESENT |
| `creature_template` | `90200`–`90203`, `90210`–`90211` | Dark Rider/Forsaken Paladin SQL | PRESENT |
| `creature.guid` | `900000`–`900003` | Dark Rider SQL | PRESENT |
| `npc_text`, `gossip_menu` | `92000`–`92003` | Dark Rider SQL | PRESENT |
| `gossip_menu_option` | `(92000..92003, OptionID=0)` | Dark Rider SQL | PRESENT |
| display dependency | `CreatureDisplayInfo=90100` | Dark Rider SQL reference | UNRESOLVED |

Loot, vendor, and conditions use composite keys. The raid vendor consumes—not
does not own—specific `ItemExtendedCost` IDs; project loot rows reference
existing creature/gameobject loot entries. See the CSV for the exact declared
dependencies.

**Observed composite deployment:** current DEV has token (`90001`) creature-loot
rows on canonical entries including `1853`, `9019`, `9568`, `10184`, `10363`,
`10440`, `10813`, `11486`, `11492`, `11501`, `11502`, `11583`, `11981`–`11983`,
`11988`, `12017`, `12056`–`12057`, `12098`, `12118`, `12259`, `12264`, `12435`,
`13020`, `14020`, `14601`, `14834`, `15339`, `15727`, and `15990`. Curio rows
exist on the expected module Naxx loot IDs and gameobject loot `361000`; these
are references, not new creature/gameobject template allocations.

The 2026-09-24 DEV query observed four Dark Rider gossip-option rows, four text
rows, 428 Dark Rider vendor composite rows, 105 Naxx40 SmartAI composite rows,
and 149 Naxx40 frozen-rune gameobject spawns. These counts establish current
deployment only; their source ownership is recorded separately in the CSV.

## Candidate availability (not yet reproducibly verified)

The source and DEV checks cover project SQL, its manifest, installed module SQL,
the current world database, and tracked DBC files where named. They do **not**
prove client MPQ parity, upstream future allocations, or untracked migrations.

| Namespace | Occupied/reserved interval | Recommended next block | Caveat |
|---|---|---|---|
| Items | project `90001`–`90005`; module `91001`–`91079` | `90006`–`90055` (10: `90006`–`90015`, 25: `90006`–`90030`, 50: `90006`–`90055`) | Available only after item/DBC/module recheck; `90001`–`90008` spell IDs are separate |
| Creature templates | `90200`–`90203`, `90210`–`90211` | `90220`–`90269` | Check current DB/module SQL before use |
| Creature GUIDs | `900000`–`900003` | `900004`–`900053` | Spawn GUID allocation must also check deployment migrations |
| NPC text/gossip menu | `92000`–`92003` | `92004`–`92053` | Menu-option identity is composite |
| Quests | module `66001`–`66018` | no project range proposed | Do not allocate in module convention |
| Naxx templates/GOs | module `351000`–`351092`; `361000`–`361001` | no project range proposed | Module-owned ranges |

These are proposed candidates from the reviewed allocations, **not verified
available blocks**: the collector currently validates occupied declarations, not
every candidate gap. No explicit undeployed project reservation was found.

A direct 2026-09-24 DEV query found no rows in the proposed item
`90006`–`90055`, creature-template `90220`–`90269`, creature-GUID
`900004`–`900053`, or NPC-text `92004`–`92053` intervals. This establishes only
current database absence; module/source/DBC-wide availability remains uncertain.

## Risks and reconciliation

- Project SQL requires DBC/client contracts for item/display/cost references;
  ownership or deployed presence of display `90100` and extended costs remains
  unresolved.
- Tracked `dbc/Item.dbc` and installed `bin/dbc/Item.dbc` have different
  SHA-256 values (`7bc097…b3b5b2e` and `d455bc…ed777d` respectively). The
  tracked `ItemDisplayInfo.dbc` and installed `CreatureDisplayInfo.dbc` are
  different DBC namespaces and cannot establish display `90100` presence.
- The project Naxx loot overlay references Individual Progression module entries;
  it does not allocate them.
- MorphSummon `91001`–`91079` is module-owned despite being in a project fork.
- Individual Progression additionally allocates Onyxia templates `301000`–`301002`
  and spell ranges `89501`, `89505`, `89507`, `89509`–`89519`, and `90001`–`90008`.
- No cleanup was performed; observed rows without provenance outside the declared
  scope remain **uncertain**, not orphaned.

## Allocation policy proposal (not a verified fact)

Before implementation, add each exact allocation or composite key to the CSV,
reserve one contiguous feature block, and record owner/source/status. Check the
live table, project manifest SQL, enabled module SQL, and every required DBC
surface. Parallel work must reserve before creating SQL. Retire allocations by
changing status with a replacement note; never silently reuse them. Regenerate
observations after migrations/module updates and review availability again.

## Method limitations

The collector checks declared IDs, not heuristically “high” database IDs; this
avoids false ownership claims but cannot discover untracked custom data. DBC IDs
are file-specific namespaces. Conditions, loot, SmartAI, and vendor records must
retain their full composite key and are not safely represented by one integer.
