# Custom ID ledger

Collected from current DEV `acore_world`, the project SQL manifest, and installed
module SQL/source on 2026-09-24. “Added by” identifies the defining source; a
reference does not claim ownership. This ledger intentionally lists allocations,
not availability or policy.

| Namespace | ID / key | What it is | Owner | Added by | DEV |
|---|---|---|---|---|---|
| Item | 90001 | Transmogrification Mark | Project | `transmog_currency_loot.sql` | present |
| Item | 90002 | Molten Core Curio | Project | `raid_gear_vendor.sql` | present |
| Item | 90003 | Blackwing Lair Curio | Project | `raid_gear_vendor.sql` | present |
| Item | 90004 | Ahn'Qiraj Curio | Project | `raid_gear_vendor.sql` | present |
| Item | 90005 | Naxxramas Curio | Project | `raid_gear_vendor.sql` | present |
| Creature template | 90200–90203 | Dark Rider raid vendors | Project | `raid_gear_vendor_npc.sql` | present |
| Creature spawn GUID | 900000–900003 | Dark Rider vendor spawns | Project | `raid_gear_vendor_npc.sql` | present |
| NPC text / gossip menu | 92000–92003 | Dark Rider dialogue and menus | Project | `raid_gear_vendor_npc.sql` | present |
| Gossip option | `(92000..92003,0)` | Dark Rider vendor options | Project | `raid_gear_vendor_npc.sql` | present |
| Creature template | 90210–90211 | Forsaken Paladin trainers | Project | `race_class_5_2.sql` | present |
| Creature display | 90100 | Dark Rider display dependency | Project reference | `raid_gear_vendor_npc.sql` | unverified DBC |
| Item | 91001–91079 | MorphSummon appearance-unlock items | `mod-morphsummon` | `data/sql/db-world/updates/mod_morphsummon_unlock_catalog_template.sql` | present |
| Creature / text / options | 601072; 601072–601074; 61072–61074 | MorphSummon NPC, text, gossip options | `mod-morphsummon` | `data/sql/db-world/base/morphsummon.sql` | module-owned |
| Quest | 66001–66018 | Individual Progression hidden state quests | `mod-individual-progression` | `src/IndividualProgression.cpp` | present |
| Creature template | 351000–351092 | Individual Progression Naxx40 templates | `mod-individual-progression` | `data/sql/world/base/naxx40_creatures.sql` | present |
| Gameobject template / spawn GUID | 361000–361001; 361101–361249 | Naxx40 objects and frozen runes | `mod-individual-progression` | `naxx40_gameobjects.sql`; `naxx40_frozen_runes.sql` | present |
| Spell | 89501,89505,89507,89509–89519;90001–90008 | Individual Progression auras/Naxx spells | `mod-individual-progression` | `adjustment_auras.sql`; `naxx40_spells.sql` | source-defined |
| Creature template | 301000–301002 | Individual Progression Onyxia templates | `mod-individual-progression` | `dungeon_onyxia.sql` | source-defined |
| Creature template | 190010–190011 | Transmog NPCs | `mod-transmog` | `trasm_world_NPC.sql` | module-owned |
| Item | 57575–57576 | Transmog UI helper items | `mod-transmog` | `trasm_world_VendorItems.sql` | module-owned |
| NPC text / spell | 601083–601084; 200100 | Transmog text / spell DBC row | `mod-transmog` | `trasm_world_texts.sql`; `trasm_world_NPC.sql` | module-owned |
| Creature template | 390011 | Chronomancer Amberwind | `mod-character-services` | `character_services_NPC.sql` | present |
| Creature template | 190012 | Ling reagent-bank NPC | `mod-reagent-bank-account` | `reagent_bank_account_NPC.sql` | present |

Project SQL also modifies canonical IDs (riding spells `33388`/`33391`, items
`6975`–`6977`, selected loot and conditions); those are overrides, not custom-ID
allocations. Full source-claim rows remain in `custom-content-registry.csv`.
