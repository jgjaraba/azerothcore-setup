# Playerbots ecosystem

## Boundary

The following independently versioned repositories form a coordinated
compatibility unit despite separate Git histories:

```text
character-services -> individual-progression
dungeon-clear      -> playerbots
multibot-bridge    -> playerbots
individual-progression ~ Playerbots-derived core lineage
```

Arrows are consumer-to-provider. The Individual Progression relationship is a
documented compatible-core/runtime relationship with bot-specific behavior, not
the same direct Playerbots-internal C++ integration used by Dungeon Clear and
MultiBot Bridge. Current revisions and worktree status are generated facts in
`../generated/ENVIRONMENT.md`.

## Shared persistence and deployment

Playerbots owns the separate `acore_playerbots` database (including its update
tracking and bot/travel/cache tables) and requires a configured database
connection. Individual Progression stores per-character state through hidden
rewarded quests and reads core character quest data. The other three create no
separate schema. Their source and module SQL/configuration must be compatible
with the selected core lineage; compiling modules alone does not establish a
deployable ecosystem.

## Components

### Playerbots

**Verified behavior.** The module supplies controllable alt bots, random bots,
and extensive combat, travel, quest, talent, guild, and management AI. Its
loader and `Playerbots.cpp` register database/player/chat/login/update hooks;
`Bot/`, `Mgr/`, `Db/`, and `Util/` hold the major subsystems. Configuration is
large; key areas are `AiPlayerbot.Enabled`, random-bot population/accounts,
alt-bot controls, summon/gear/loot/quest/combat behavior, logging, command
server, and Playerbots database updates.

**Structure.** `src/Script/playerbots_loader.cpp` registers `Playerbots.cpp`;
`src/Bot/`, `Mgr/`, `Db/`, and `Util/` provide AI, management, persistence, and
supporting services.

**Compatibility.** Its README requires a Playerbots core fork rather than stock
AzerothCore. The local core/module combination has not been compiled or tested
as a compatibility proof. Core player/database hooks and Playerbots internal
APIs are high-risk update surfaces. Its world/character data changes survive
module disablement.

**Open questions.** The compatible core revision and Playerbots database grant/
update state are not recorded as durable deployment inputs.

### Individual Progression

**Verified behavior.** Progression tiers use hidden quests (`66000 + state`) and
cover visibility/access, historical instance scripts, attunements, PvP,
spells, and Vanilla/TBC power/healing adjustments. The singleton in
`IndividualProgression.cpp` is used by its awareness, player, spell, PvP, and
content-script groups. Configuration includes enablement/group rules, tier
power/healing, bot-only adjustments, attunements, RDF, spell/class behavior,
and core-setting overrides. Optional world data changes many core tables;
runtime state uses `characters` and `character_queststatus_rewarded`.

**Structure.** `src/IndividualProgression.{h,cpp}` is the central singleton;
awareness/player/spell/PvP files and `vanillaScripts/`, `naxx40Scripts/`,
`tbcScripts/`, and `wotlkScripts/` hold registered content behavior.

**Project integration.** Source has bot-account paths and the README documents
Playerbots/NPCbots support. Project custom riding and mount-condition overlays
intentionally replace part of its world data; its Naxx40 custom IDs are a
prerequisite for raid-curio loot.

**Compatibility.** Its README requires the Grimfeather lineage based on a
Playerbots fork and asks for core settings such as `EnablePlayerSettings` and
DBC attribute behavior. Enabling/disabling configuration does not reverse
optional database changes. Hidden quest IDs and optional DBC/client data need
collision and deployment checks.

**Open questions.** The exact optional SQL/DBC set deployed and its compatibility
with the local core are unverified.

### Character Services

**Verified behavior.** NPC `390011` offers configurable paid rename,
appearance, race, faction, and progression-tier actions. Standard services set
core login flags. Tier purchases directly include `IndividualProgression.h` and
call its progression/account/phase APIs; the deliberate tier-11 skip is encoded
in source. World SQL owns only this NPC/template/model.

**Structure.** `src/CS_loader.cpp` registers `src/CharacterServices.cpp`; its
only tracked data is `data/sql/db-world/character_services_NPC.sql`.

**Compatibility.** This is a hard Individual Progression API dependency. Its
template controls service enablement, account-unlock policy, dynamic cost, and
per-service/tier costs. The installed ignored configuration is project-specific
runtime state, not semantic documentation. Entry `390011` installation is
destructive for that reserved entry; no migration path was found.

**Observed deployment state (2026-09-20).** One `creature_template` row for
entry `390011` exists in local DEV. This does not establish installation
provenance, configuration usability, or in-game behavior.

### Dungeon Clear

**Verified behavior.** Dungeon Clear adds Playerbot strategies, actions,
triggers, values, pathing, pulls, events, bosses, commands, addon support, RDF
queue filling, and optional test runs to autonomously clear dungeons/raids. It
registers contexts in Playerbots class registries and uses core/playerbot hooks.
`DungeonClear.Enable` and configuration groups cover recovery, regrouping,
healing repositioning, pulls, event timeouts, heroic/raid overrides,
pathfinding, queue fill, logging, and test drivers.

**Structure.** `DungeonClearModule.cpp`, command/addon-hook sources,
`Ai/Dungeon/DungeonClear/`, `DungeonQueueFill/`, and `TestRun/` form the main
subsystems; `mod_dungeon_clear.cmake` adds optional tests.

**Compatibility.** It directly depends on Playerbots internals and is therefore
especially update-sensitive. Enablement is latched at startup because contexts
are registered then; restart after changes. The `DC` addon protocol and navmesh
data are client/runtime contracts. It has no database schema. Existing
Zul'Farrak/Sunken Temple ID workarounds need reassessment when core scripts
change.

**Open questions.** Companion-addon revision, navigation fixture availability,
and combined Playerbot live behavior were not validated.

### MultiBot Bridge

**Verified behavior.** This server-side Playerbots bridge accepts validated
`MBOT` addon messages from MultiBot-Chatless and exposes scoped inventory,
bank, loot, talents, profession, quest, group, roster, outfit, and bot actions.
It has payload validation, capability negotiation, rate limits, and replay
protection; it is not an arbitrary command executor. Its own template only
controls console logs, while source also consumes Playerbots settings. It owns
no tables but reads and mutates native character persistence, including
`characters`, `character_queststatus`, `item_instance`, `guild_bank_right`, and
`guild_bank_item`, in addition to `arena_team` and `arena_team_member`.

**Structure.** `src/mod_multibot_bridge.cpp` registers the PlayerScript in
`src/MultiBotBridge.cpp`, which implements message parsing, capability handling,
and Playerbot/core operations.

**Compatibility.** Direct Playerbots APIs and the version-1, 255-byte addon
wire contract are update boundaries. Companion addon revision and advertised
feature matching were not audited. It shares Playerbots with Dungeon Clear but
uses a distinct protocol and has no direct source coupling to it.

**Open questions.** Companion-addon revision and complete advertised feature
matching remain unverified; native character/bank schema and APIs are additional
update-sensitive dependencies.

## Operational exclusion

AH Bot Plus is outside this cluster but its configured auction characters must
not be Playerbots. Preserve that account/character segregation as an operational
invariant when adding random bots or AH bot GUIDs.

## Coordinated update and validation

Before an update, back up every affected database; record compatible core and
module revisions; apply module database updates (including Playerbots) before
project overlays; then recheck configuration, addon protocols, and client/DBC
assets. Build compatibility and live behavior have not been verified in this
audit. At minimum validate Playerbot login/random population, an Individual
Progression tier transition, Character Services tier purchase, Dungeon Clear
strategy registration, and a MultiBot capability exchange in a disposable
development environment.

## Open questions

- The exact supported core/Playerbots/Individual Progression revision matrix is
  not tracked as a durable compatibility baseline.
- Effective ignored configuration and Playerbots database grants are not
  project-controlled documentation.
- No live-stack validation demonstrates combined AI, progression, addon, or
  service behavior.

## Evidence

Verified from the five module repositories' READMEs, configuration templates,
loaders, source, and SQL on 2026-09-19. Repository revisions are intentionally
not duplicated here.
