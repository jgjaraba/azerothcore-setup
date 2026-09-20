# Modules

## Scope and source of truth

This is the semantic catalog for independently versioned repositories below
`~/azerothcore/modules/`. `generated/ENVIRONMENT.md` is authoritative for the
current module inventory, remotes, branches, revisions, and working-tree state.
Local runtime configuration values are ignored deployment state; this document
records configuration surfaces, not assumed effective values.

## Relationship index

| Consumer | Provider | Verified relationship | Failure mode |
|---|---|---|---|
| Character Services | Individual Progression | Direct C++ API | Build failure or tier mismatch |
| Dungeon Clear | Playerbots | Playerbot internal contexts and registries | Build or AI regression |
| MultiBot Bridge | Playerbots | Playerbot APIs and addon bridge | Build, authorization, or protocol regression |
| Individual Progression | Playerbots lineage | Compatible fork and bot-aware paths | Unsupported combination |
| AH Bot Plus | Playerbot characters | AH characters must not be Playerbots | Documented crash risk |
| Custom riding SQL | Individual Progression | Post-module world-data override | Module update restores requirements |
| Raid-curio loot SQL | Individual Progression Naxx40 data | Custom creature/gameobject identifiers | Missing rewards |
| Transmog-token SQL | Transmog | Project item/configuration contract | Token drops but is not charged |

`playerbots-ecosystem.md` documents the first four relationships as a
coordinated compatibility unit. `custom-world-sql.md` records the data-overlay
relationships.

## Installed module catalog

| Module | Verified responsibility | Persistence | Configuration template | Detail |
|---|---|---|---|---|
| AH Bot Plus | Auctions | Core AH/mail data | `mod_ahbot.conf` | Standalone |
| Character Services | Paid services/tier NPC | World NPC/login flags | `character_services.conf` | Ecosystem |
| Dungeon Clear | Playerbot dungeon AI | No SQL | `mod_dungeon_clear.conf` | Ecosystem |
| Individual Progression | Expansion tiers | Core quest/world data | `individualProgression.conf` | Ecosystem |
| MorphSummon | Summon models | World NPC/character weapon | `morphsummon.conf` | Standalone |
| MultiBot Bridge | Addon bridge | Native character/item/bank | `MultiBotBridge.conf` | Ecosystem |
| Playerbots | Alt/random bot AI | Playerbots DB/core data | `playerbots.conf` | Ecosystem |
| Quest Loot Party | Quest loot hook | World module strings | `mod-quest-loot-party.conf` | Standalone |
| Reagent Bank Account | Account reagent storage | World NPC/character table | Reagent Bank config | Standalone |
| Transmog | Appearances/costs | Character/world/auth data | `transmog.conf` | Standalone |

All use the core module CMake discovery/loader mechanism. Playerbots additionally
causes `MOD_PLAYERBOTS` definitions in `modules/CMakeLists.txt`; Dungeon Clear
also provides `mod-dungeon-clear.cmake` for its optional test target.

## Standalone modules

### AH Bot Plus

**Verified behavior.** `AuctionHouseBot.cpp` and its world, auction, mail, and
command scripts maintain configurable seller/buyer auctions. Relevant template
areas are bot GUIDs, cycle timing, expiry/mail handling, pricing multipliers,
listing filters/stacks/drop-rate weighting, and buyer limits. It has no module
schema or migrations: configured ordinary character GUIDs, core auction/mail
data, item data, and world loot data are its persistence boundary.

**Structure.** `src/ah_bot_loader.cpp` registers the main engine
(`AuctionHouseBot.{h,cpp}`) and world/auction/mail/command hooks in
`AuctionHouseBotScript.cpp`.

**Compatibility and project concerns.** It is sensitive to auction, mail, item,
and hook APIs. `ReturnExpiredAuctionItemsToBot` can retain item/mail data. The
template and README explicitly prohibit Playerbot characters; reserve separate
ordinary characters for this role. No direct source coupling to other installed
modules was found beyond that exclusion.

**Unresolved / recommendation.** No current AH character allocation or effective
configuration was audited. Validate configured GUIDs are ordinary characters
before enabling it after playerbot or core updates.

### MorphSummon

**Verified behavior.** `morphsummon.cpp` provides creature gossip and
player/pet hooks for Warlock, Death Knight, and Mage permanent-summon models and
Felguard virtual weapons. Template options cover enablement, announcements,
renaming, category model lists, Felguard weapons, and visual/equipment effects.
Upstream data owns NPC `601072`, menus/text `61072`–`61074`, and character table
`mod_morphsummon_felguard_weapon`; it also reads core item/creature/equipment
data.

**Structure.** `src/loader_morphsummon.cpp` registers the single principal
implementation in `src/morphsummon.cpp`; base world and character SQL are under
`data/sql/db-world/base/` and `data/sql/db-characters/base/`.

**Project-specific customization.** A pending non-upstream customization adds
appearance-unlock character/world tables, custom item IDs `91001`–`91079`, loot
acquisition, and gossip filtering. This is not established upstream behavior;
the source and all related SQL must be deployed together if retained. Generated
environment state is authoritative for its repository status and local IDE data.

**Observed deployment boundary (2026-09-20).** DEV contains
`mod_morphsummon_appearance_catalog` (90 enabled appearances, 11 defaults),
`mod_morphsummon_unlock_requirements` (79 rows for items `91001`–`91079`), and
the matching character unlock table. All 79 item templates exist, but the
observed character unlock table is empty. This establishes deployed schema/data,
not successful unlock behavior, provenance, or safe rerun semantics. The
catalog, requirements, item/loot definitions, character schema, module source,
and effective configuration form one update/deployment unit.

**Compatibility and unresolved questions.** The pending SQL copies current
schema/data and needs ID-collision and rerun checks. The base module is tied by
its documentation to a specific core era. No build, migration, or in-game
unlock test was performed. There is no verified direct interaction with the
other installed modules.

### Quest Loot Party

**Verified behavior.** The `OnPlayerBeforeFillQuestLootItem` player hook marks
only normal-quality quest loot `freeforall`; eligibility still comes from the
core quest-loot path. `QuestParty.Enable` and `QuestParty.Message` are its
configuration surface. Its world base SQL owns module-string ID `1` and locales;
it creates no gameplay schema.

**Structure.** `src/QLP_loader.cpp` registers `src/qlp_main.cpp`; base world SQL
is `data/sql/db-world/base/qlp_2026_04_19_00.sql`.

**Compatibility and project concerns.** The core must retain the quest-loot
hook and `LootItem::freeforall`. The README's configuration filename differs
from the tracked template (`mod-quest-loot-party.conf.dist`); deploy the tracked
name. Dungeon Clear also affects bot loot processing, but no direct module
coupling or combined live validation was found.

**Open questions.** Source relies on the core to invoke its hook only for
eligible quest loot; live party distribution behavior has not been tested.

### Reagent Bank Account

**Verified behavior.** NPC `190012` deposits eligible stackable trade goods/gems
into account-wide `custom_reagent_bank_account` and supports category browsing,
pagination, and stack withdrawal. World SQL owns the NPC/template; character
SQL owns `(account_id, item_entry)` storage. Source uses character-DB reads and
transactions for aggregate deposits.

**Structure.** `src/ReagentBankAccount_loader.cpp` registers
`src/ReagentBankAccount.cpp`; world NPC and character-table base SQL are in the
corresponding `data/sql` subtrees. No README was found.

**Compatibility and project concerns.** The template exposes
`ReagentBankAccount.Enable`, but inspected source never reads it: the script is
always registered when installed. Base SQL has no migration path. Database
failure behavior after inventory destruction and stale/invalid item rows were
not validated. No direct module interaction was found.

**Open questions.** Installation/placement, invalid-item handling, and database
failure recovery are undocumented and untested.

### Transmog

**Verified behavior.** Player/item scripts, gossip, portable UI, commands, and
character DB code implement transmogrification, appearance collections, hidden
appearances, and presets. Key template groups cover enablement/UI, collection
tracking, restrictions, pricing, and `RequireToken`/`TokenEntry`/`TokenAmount`.
Character tables are `custom_transmogrification`,
`custom_transmogrification_sets`, and `custom_unlocked_appearances`; module
world/auth SQL supplies NPC/text/vendor/module-string/subscription data.

**Structure.** `src/transmog_loader.cpp` registers the main
`Transmogrification.{h,cpp}` implementation, `transmog_scripts.cpp`, and
`cs_transmog.cpp`; schema/data/migrations are under `data/sql/db-characters`,
`db-world`, and `db-auth`.

**Project-specific customization.** `custom-world-sql.md` defines item `90001`
and its loot as a project transmog token. Module source does not define that
item. It becomes a cost only when ignored runtime configuration explicitly
enables token charging and selects it; the template defaults do not establish
that deployment state.

**Observed effective setting (2026-09-20).** The ignored DEV configuration sets
`RequireToken = 1`, `TokenEntry = 90001`, and `TokenAmount = 2`; module source
loads these exact keys. This establishes intended runtime charging parameters,
not successful token consumption or live usability.

**Compatibility and unresolved questions.** Module SQL/migrations must precede
use, and subscription migration may require `mod-acore-subscriptions`. NPC-text
ownership is core-version-sensitive. No direct coupling to MorphSummon or
Individual Progression was found. Live usability remains unverified.

## Cross-cutting update safety

Treat core, Playerbots ecosystem modules, module SQL across their respective
databases, ignored runtime configuration, and client/addon protocols as one
explicit compatibility exercise. Module base SQL is not necessarily reversible
or automatically installed. Reapply project world overlays only after checking
their source data and required module data; the custom SQL manifest encodes
project-file order but remains a post-module overlay. No tracked workflow
currently backs up, updates, rebuilds, migrates, validates, or rolls back this
full set.

## Evidence

Module READMEs, configuration templates, `src/` loaders/registrations, and
`data/sql/` were inspected on 2026-09-19. This document deliberately defers
transient Git facts to the regenerated environment inventory.
