# Task: Forsaken Paladin Class Quests

Status: PHASE 2.1 COMPLETE — READY FOR COMMIT
Created: 2026-09-21
Last updated: 2026-09-22 (Phase 2.1 started)
Mode: implementation

## Goal

Implement the approved bilingual Forsaken Paladin class-quest design and prepare
its Item.dbc handoff. Human in-game QA has accepted Phase 2.1; client patch-Z
packaging remains a separate release responsibility.

## Scope and boundaries

- Writable repository: `/home/dev/azerothcore-setup` on
  `feat/forsaken-paladin-class-quests`, initially at
  `1886cae9378593dc08d3e8b4e1d8521c64306e8a` with pre-existing task artifacts.
- The AzerothCore checkout remains read-only on protected `master`; preserve its
  three pre-existing player-owned combo-point changes.
- Project SQL, Item.dbc generation, and local DEV database/runtime validation are
  authorized. Do not modify IP, Playerbots, production, or final client MPQs.
- Do not stage, commit, push, open a PR, or run `/finish-task`.

## Frozen verified baseline

- **IMPLEMENTED + VERIFIED:** human in-game validation confirmed Abraham West
  and Pancratius Ward behave correctly.
- `data/sql/custom/db_world/forsaken_paladin.sql` is the sole canonical baseline
  owner for Undead Paladin creation data, outfits, trainers, models, equipment,
  locales, addons, and exact trainer spawns.
- No baseline DBC change is required. Do not reopen or redesign the baseline
  unless subsequent quest work exposes a concrete regression.

## Authoritative design state

- `forsaken-paladin-class-quests.DESIGN.md` is the sole authoritative final
  design for future Phase 2.1 work. `PHASE2B.md` is explicitly marked
  `SUPERSEDED — NOT AUTHORITATIVE` and is traceability only.
- The final design uses quest IDs `91010`–`91016` and `91020`–`91024`; DEV
  evidence found these quest IDs free, while the numerically overlapping item
  IDs are occupied and must not be used for custom items.

## Fixed decisions

- Custom quest items are permitted where an existing location and actor provide
  credible provenance. Required Item.dbc changes are allowed; the human manually
  packages server/client records into regular and HD patch-Z as applicable.
- `Lordaeron's Vigil` / `Vigilia de Lordaeron` is a Verigan's Fist-equivalent
  level-20 sidegrade. A final DisplayID is a non-blocking human visual choice;
  a valid existing display may be provisional in the design.
- Ambermill, custom fallen Deathguard/Symbol of Life target, Ivar combat event,
  invisible controller, Melrache/bodyguard or quest-372 changes, Springvale
  ember, IP changes, and Playerbots changes are rejected.
- Redemption is not a hard prerequisite for the level-20 chain. The final quest
  design must use ordinary DB mechanisms, coexist with canonical quests, and
  support a human player accompanied by Playerbots without bot-specific logic.

## Retained evidence

- Canonical Redemption ends at quest `1788`; its reward behavior is reproduced
  by 91016. Symbol of Life `6866`/spell `8593` are not used by the custom chain.
- Canonical `429 → 430 → 425` makes the Ivar the Foul kill duplicative; Ivar
  Patch is removed from the final route.
- Fenris/Thule Ravenclaw `1947` is an approved viable anchor for one modest,
  additive, quest-conditioned custom item. Do not alter Thule's Head `3623`,
  quest `442`, canonical loot, pickpocket data, AI, spawns, or events.
- Item allocation, source data, Item.dbc contract, IP classification, loot
  semantics, reward parity, and bilingual text are closed in DESIGN, pending
  implementation-time/live validation only.

## Serialized workflow

1. `ac-research`: resolve only remaining design evidence and DBC contracts.
2. Checkpoint findings in this plan.
3. `ac-architecture`: produce the complete final bilingual DESIGN.
4. Checkpoint the design decision.
5. `ac-review`: adversarial review of that DESIGN only.
6. Checkpoint review findings.
7. Synthesize ordinary fixes, readiness matrix, DBC handoff, and next action.

## Validation and mutation log

- PASS — baseline manifest validation, four successful canonical SQL applications,
  targeted DEV queries, SQL codestyle, independent review, and human in-game
  validation completed before this design phase.
- 2026-09-22 — environment state refreshed for this closure. No database,
  runtime, build, configuration, DBC, or quest-data mutation has occurred.

## Current checkpoint

- Durable plan hygiene normalized: each canonical plan section appears once;
  frozen baseline status, current authority, retained evidence, and constraints
  are recorded above.
- Stage 1 delegated research established item IDs `92060`–`92064`, removes Ivar
  Patch, uses Thule `1947`, Agamand Weapon Rack `105172`, Syndicate Watchman
  `2261`, and Rot Hides `1939`/`1940`/`1942`/`1943` as additive component
  sources, and retains ordinary-service Redemption with 1788 reward parity.
  It established the Item.dbc/server/regular-client/HD-client contract and
  per-recipient core quest-loot behavior; orchestration completed the bounded
  DEV and tracked-DBC checks afterwards.

## Stage 1 checkpoint

- **IDs:** local DEV queries found no `item_template`, quest, creature template,
  gameobject template, creature, or gameobject rows in the proposed item range
  `92060`–`92064`; tracked project SQL has no use of the range. The tracked
  `dbc/Item.dbc` dry run also found all five IDs absent and cloneable.
- **DBC contract:** each custom component must be a new Item.dbc record cloned
  from ordinary quest item `7309`; the weapon must clone Item.dbc record `6953`.
  Matching `item_template` data and generated records must be deployed server
  side and manually packaged by the human into both regular and HD patch-Z.
  No installed server Item.dbc was found. Both existing MPQs are present but the
  local 7-Zip implementation cannot open them, so their current record contents
  are UNKNOWN; that does not prevent generating the required replacement rows in
  Phase 2.1.
- **mechanics:** quest `1788` is Paladin-only, level `-1`/minimum `12`, follows
  `1787`, has `RewardXPDifficulty=6`, no money/items, display spell `7328`, and
  reward spell `7329`. The final Redemption conclusion copies those reward
  semantics; it has no Symbol of Life target or custom resurrection mechanic.
- **sources:** Thule `1947` (level 24), Agamand Weapon Rack `105172`/loot `4767`,
  Syndicate Watchman `2261` (level 20–21), and Rot Hides 1939/1940/1942/1943
  (levels 16–19) have ordinary DEV spawns and existing loot. The existing IP zone
  data includes some of these templates but no target-specific phasing condition
  was found; classify the final sources SAFE for current ordinary-world use,
  subject to Phase 2.1 live validation in the selected IP state.
- **loot:** implement each source as additive `QuestRequired=1`, `LootMode=1`,
  `GroupId=0`, `MinCount=MaxCount=1`, and a quest condition. Core builds creature
  quest loot per eligible nearby group member, and the installed quest-loot-party
  hook makes normal-quality quest loot free-for-all. The Agamand rack uses
  personal loot, so each eligible player must interact serially after its normal
  respawn. Playerbots are ordinary group players; human-plus-bot loot remains a
  Phase 2.1 validation item.
- **route:** Ivar Patch is removed because its existing kill objective duplicates
  `429 → 430 → 425` and no distinct ordinary alternative was evidenced.

## Stage 2 checkpoint

- **Architecture decision:** retain a database-only quest design plus five
  Item.dbc records; no module, core change, SmartAI, event, controller, new
  world actor, or canonical-content modification is required.
- **Redemption shape:** `91010` Pancratius→Abraham; `91011` ten Linen Cloth to
  Caice; `91012` Caice→Abraham; `91013` Abraham→Sevren; `91014` eight Scarlet
  Warriors 1535; `91015` Sevren→Abraham; `91016` Abraham conclusion with exact
  1788 reward semantics. Each quest is Undead Paladin-only, minimum level 12,
  and uses only ordinary talk/item/kill mechanisms. The final conclusion teaches
  Resurrection through its reward, not a custom target or Symbol encounter.
- **Weapon shape:** independent level-20 `91020` Abraham→Basil, `91021`
  Agamand Weapon Haft 92061 plus Rot Hide Binding 92063, `91022` Ravenclaw
  Counterweight 92060, `91023` Durnholde Forged Iron 92062, and `91024` Basil
  conclusion rewarding only Lordaeron's Vigil 92064. The source locations are
  Agamand Mills, Silverpine Rot Hides, Fenris Isle, and Durnholde; Ivar Patch is
  absent. The components are ordinary reclaimed materials, not relics.
- **item contract:** `92060`–`92063` clone ordinary quest item 7309; `92064`
  clones every gameplay-relevant field of Verigan's Fist 6953 and uses existing
  provisional DisplayID 13466. All five require `item_template`, esES locale,
  server Item.dbc, and matching regular/HD patch-Z Item.dbc records.
- **implementation contract:** custom component loot is 100%, additive,
  quest-required, `LootMode=1`, `GroupId=0`, count one, with an active-quest
  condition and source-table registration as required. Final implementation must
  verify effective source loot IDs before inserting rows and must preserve all
  canonical loot.
- **text/design:** `ac-architecture` supplied complete concise enUS/esES player
  text and per-quest fields, plus the four component provenance analysis. It is
  now serialized in the rewritten authoritative DESIGN. The former Phase2B
  proposal is marked `SUPERSEDED — NOT AUTHORITATIVE`.
- **Stage 3 review:** identified incomplete text, stale PLAN authority wording,
  an incorrect shared-loot claim for the personal Agamand rack, and insufficient
  condition-key detail. The text, authority state, rack contract, and exact
  condition/quest-item registration contract were corrected. The reviewer found
  no banned content and confirmed the IDs, 1788 reward fields, and Verigan
  parity target.
## Stage 3 and Stage 4 synthesis

- `ac-review` completed the adversarial review of only the authoritative DESIGN
  and PLAN. It found two BLOCKER/MAJOR classes of defects: truncated bilingual
  text and stale authority state; plus the personal Agamand rack behavior and
  incomplete loot-condition key contract. All were corrected. A narrow rereview
  found no remaining BLOCKER or MAJOR.
- No quest SQL/data, item/loot/condition rows, Item.dbc records, client patches,
  builds, runtime changes, commits, or pushes were made in this design phase.

| Area | Status | Evidence / Decision |
|---|---|---|
| Baseline | IMPLEMENTED + VERIFIED | Human in-game validation; `forsaken_paladin.sql` frozen canonical owner |
| Redemption chain | READY FOR PHASE 2.1 | 91010–91016 full bilingual ordinary-service design |
| Level-20 chain | READY FOR PHASE 2.1 | Independent 91020–91024 four-component route |
| Quest IDs | READY FOR PHASE 2.1 | DEV-observed free quest IDs |
| Quest count | READY FOR PHASE 2.1 | 12 steps have distinct place, objective, or consequence |
| Item IDs | READY FOR PHASE 2.1 | 92060–92064 DEV/tracked/DBC dry-run collision evidence |
| Agamand component | READY FOR PHASE 2.1 | 92061, personal rack interaction contract recorded |
| Rot Hide component | READY FOR PHASE 2.1 | 92063, four ordinary creature sources |
| Fenris/Thule component | READY FOR PHASE 2.1 | 92060 from Thule 1947; canonical 3623/442 untouched |
| Durnholde component | READY FOR PHASE 2.1 | 92062 from Watchman 2261; no quest-372 interaction |
| Final weapon | READY FOR PHASE 2.1 | 92064 is an exact Verigan gameplay sidegrade |
| Reward parity | READY FOR PHASE 2.1 | 91016 contract reproduces 1788 reward fields |
| IP reachability | READY FOR PHASE 2.1 | Selected sources SAFE; live selected-state check remains implementation validation |
| Additive loot | READY FOR PHASE 2.1 | Exact ownership, source keys, and condition shape recorded |
| Group semantics | READY FOR PHASE 2.1 | Creature per-recipient rules and rack serial exception recorded |
| Playerbots scope | READY FOR PHASE 2.1 | Ordinary accompaniment only; no bot changes |
| Item.dbc | READY FOR PHASE 2.1 | Five required clone records and deployment contract recorded |
| Other DBCs | NOT APPLICABLE | Existing NPCs, objects, spells, and display reused |
| enUS text | READY FOR PHASE 2.1 | Complete authoritative text rereviewed |
| esES text | READY FOR PHASE 2.1 | Complete European Spanish text rereviewed |
| Durable DESIGN | READY FOR PHASE 2.1 | DESIGN is sole authority; Phase2B explicitly superseded |
| Weapon DisplayID | HUMAN VISUAL CHOICE | Provisional valid existing DisplayID 13466; non-blocking |

**READY FOR PHASE 2.1.**

## Phase 2.1 Stage 1 checkpoint

- Preflight reconfirmed the frozen baseline templates, free quest IDs, free item
  IDs, ordinary source loot IDs, and the live current schemas. No baseline
  regression was found.
- Added manifest-owned `forsaken_paladin_quests.sql` after the baseline. It owns
  the Phase 2.1 content; the frozen baseline file is unchanged.
- Applied the custom item rows `92060`–`92064` and esES item locales to local
  `acore_world`. Components use 7309's quest-item shape; 92064 copies the
  required 6953 gameplay fields with DisplayID 13466.
- Added `dbc/forsaken_paladin_item_dbc_mapping.csv`, generated the five Item.dbc
  records with the project tool, updated tracked `dbc/Item.dbc`, and installed
  the identical generated Item.dbc to `env/dist/bin/dbc/Item.dbc`. No MPQ was
  modified. The human must later package this tracked `dbc/Item.dbc` into both
  regular and HD patch-Z archives.
- DEV mutation log: applied the item-only Stage 1 SQL once and replaced the DEV
  server Item.dbc with the generated 46,106-record file.

## Next exact action

Leave the completed Phase 2.1 task-owned files ready for human staging and
commit. Client patch-Z packaging/deployment remains a separate release task.

## Redemption correction checkpoint

- Corrected talk/travel semantics after technical review. Quests 91010, 91012,
  91013, and 91015 now have no RequiredNpcOrGo objective and are completed only
  through their ordinary quest-ender relation. The intended objective matrix is:

  | Quest | Intended objective | DB representation |
  | --- | --- | --- |
  | 91010 | travel/talk to Abraham | quest ender only |
  | 91011 | Linen Cloth x10 | RequiredItem 2589 x10 |
  | 91012 | return to Abraham | quest ender only |
  | 91013 | travel/talk to Sevren | quest ender only |
  | 91014 | kill Scarlet Warrior x8 | RequiredNpcOrGo 1535 x8 |
  | 91015 | return to Abraham | quest ender only |
  | 91016 | immediate instruction/reward | no fake creature objective |

- Added project-owned esES rows to `quest_request_items_locale` for Progress
  text and `quest_offer_reward_locale` for Completion dialogue. Added targeted
  cleanup for both tables. `quest_template_locale` now maps Title, Details,
  Objectives, EndText (AreaDescription), CompletedText (QuestCompletionLog),
  and ObjectiveText1; it does not carry NPC dialogue.
- DEV mutation log: reapplied the complete custom SQL twice after correction;
  both applications succeeded. Manifest validation and whitespace validation
  passed. Direct DB queries confirmed all locale surfaces and no friendly NPC
  is a RequiredNpcOrGo target.
- 92064 versus 6953 parity: queried all gameplay columns. Only `entry` (92064
  versus 6953) and `name` (Lordaeron's Vigil versus Verigan's Fist) differ.
  DisplayID 13466, class restriction, stats, weapon values, durability,
  disenchant data, flags, and VerifiedBuild are identical.
- Narrow independent review passed with no concrete defects in objective
  semantics, locale mapping, or 92064 parity.

## Phase 2.1 Redemption checkpoint

- Added custom-only Redemption quests 91010–91016, their class/race gates,
  predecessor and follow-up chain, ordinary creature relations, objectives,
  English quest text, and complete esES localization to
  `forsaken_paladin_quests.sql`.
- Quest 91011 consumes Linen Cloth (2589) x10. Quest 91014 uses ordinary shared
  Scarlet Warrior (1535) kill credit x8. Quest 91016 mirrors 1788's reward
  semantics: XP difficulty 6, DisplaySpell 7328, Spell 7329, and quest flag 8
  (`QUEST_FLAGS_SHARABLE`); it is objective-free and completes normally at
  Abraham.
- DEV mutation log: reapplied the custom SQL twice; the second application
  succeeded, confirming idempotency for the implemented Stage 1 and Redemption
  data.
- Validation: manifest validation passed; direct database queries confirmed all
  seven quest settings, relations, and esES locale rows. No server reload or
  runtime quest interaction has been performed.

## Phase 2.1 weapon-chain completion checkpoint

- Verified Agamand Weapon Rack `105172` source data in current DEV: type `3`,
  `data1`/loot ID `4767`, live spawn `45165`, 120-second respawn, and existing
  personal quest loot. Verified creature source loot IDs `1939`, `1940`,
  `1942`, `1943`, `1947`, and `2261` match their template entries.
- Implemented `91020`–`91024`, all relations, enUS/esES template/progress/
  completion text, component objectives, and final 92064 reward in
  `forsaken_paladin_quests.sql`. Added seven exact, additive 100% quest loot
  rows, active-quest conditions, and quest-item registrations. Canonical loot
  rows remain untouched.
- Startup validation exposed missing questgiver flags on existing actors
  `2307`, `4605`, `90210`, and `90211`. The script now safely applies
  `npcflag | 2`, preserving their existing flags/services. Direct queries
  confirmed zero custom quest relations target an actor without the flag.
- Independent review found one MINOR deletion-scope defect: creature cleanup
  predicates formed cross-products that could delete future project rows. It
  was corrected to the exact owned tuples. A follow-up subagent rereview could
  not run because the review-agent usage limit was reached; direct SQL review
  and two successful complete manifest reapplications revalidated the fix.
- PASS — `apply-db-world.sh --validate`; complete manifest application twice
  after the final fix; targeted count/field queries (five weapon quests, seven
  loot rows, seven conditions, seven registrations); `git diff --check`; and
  AzerothCore SQL codestyle. `python` was unavailable; the required SQL linter
  passed under `python3`.
- FAIL (unrelated) — AzerothCore C++ codestyle scans existing untouched core
  files and reports pre-existing formatting/qualifier violations outside this
  database-only task. No C++ file was modified.
- PASS — DEV authserver/worldserver final restart and status: auth PID `28052`,
  world PID `28062`. Bounded recent Server/Errors log inspection showed no
  custom quest/item, SQL, or missing-questgiver errors. The only observed
  non-custom diagnostics were process-priority permission and recurring auth
  realm-resolution messages. No build was needed for this database-only change.
- DEV mutation log: complete custom world manifest applied repeatedly during
  validation (including the two final successful passes); both servers were
  restarted three times. Current DEV database contains the final quest data and
  both servers are running. No production or client MPQ was modified.

## Human in-game QA handoff

1. Install/package the tracked `dbc/Item.dbc` into matching regular and HD
   client patch-Z archives before testing item names/icons/weapon display.
2. With an Undead Paladin, verify only that race/class sees both chains:
   Pancratius starts 91010 at level 12; Abraham starts independent 91020 at
   level 20. Verify non-Undead and non-Paladin characters do not receive them.
3. Complete 91010–91016 in order: Pancratius → Abraham → Caice (Linen Cloth
   x10 consumed) → Abraham → Sevren (Scarlet Warrior x8 shared credit) →
   Abraham. Confirm all English and esES details, progress, completion text,
   objectives, and map/log text; confirm 91016 immediately completes at Abraham
   and teaches Resurrection without a Symbol of Life target.
4. Complete 91020–91024: Abraham → Basil; while 91021 is active, obtain one
   92061 from Agamand Weapon Rack 105172 and one 92063 from any Rot Hide;
   confirm both are consumed at Basil. Then obtain 92060 only while 91022 is
   active from Thule 1947, and 92062 only while 91023 is active from Watchman
   2261. Confirm no component drops when its matching quest is inactive.
5. Group-test creature component loot with a human plus Playerbot: each eligible
   player should receive normal quest loot independently/free-for-all. Test the
   rack separately: it is personal loot, so each eligible player must interact
   serially after its normal respawn; one interaction must not award both.
6. Confirm 91024 immediately completes at Basil, awards exactly one 92064 and
   no alternate item/spell, consumes no extra material, and that the weapon's
   visible model/display, stats, binding, locale name, equip behavior, and
   inventory/client rendering are correct in both client variants.

## Remaining pre-merge action

Complete — final `ac-review` ran after human QA acceptance. It found four MINOR
documentation/ownership defects; all were corrected and a narrow rereview found
only the now-corrected stale QA status. No BLOCKER or MAJOR remains. Harness
policy edits are unrelated pre-existing changes and must be excluded from this
feature's merge.

## Final pre-merge review checkpoint

- Final review covered the complete Phase 2.1 diff for correctness, update
  safety, project ownership, destructive cleanup, SQL idempotency,
  quest/locale/loot/condition consistency, DBC ownership, and unrelated files.
- Four MINOR findings were corrected: stale design status, an incorrect
  `QUEST_FLAGS_SHARABLE` description, incomplete identifier/client-DBC
  registration, and explicit classification of unrelated harness changes.
- PASS — final narrow `ac-review` reported no findings. No BLOCKER or MAJOR
  remains. **PHASE 2.1 COMPLETE — READY FOR COMMIT.**

## Runtime diagnostic checkpoint

- 2026-09-22 — Worldserver stopped with a bounded-log assertion
  `ASSERT_NOTNULL_IMPL: LookupEntry(id)`. The initial suspicion that custom
  CreatureDisplayInfo `90100` was absent is disproven: the installed
  `CreatureDisplayInfo.dbc` contains `90100`, its ModelId `49` exists in
  `CreatureModelData.dbc`, and all 21,385 current DB
  `creature_template_model` display IDs exist in the installed display DBC.
  The assertion does not identify the lookup type or ID, so its root cause is
  UNKNOWN and cannot be attributed to the Forsaken Paladin quests. No project
  data, DBC, source, or runtime state was modified during this diagnostic.
- 2026-09-22 — Bounded runtime inspection found effective
  `Console.Enable = 1` caused a continuous `AC>` prompt loop in managed,
  noninteractive `worldserver.out` (1.8 GiB). Set effective DEV
  `Console.Enable = 0`, restarted worldserver, and observed it running for two
  minutes without log growth or a new assertion. Authserver remained running.
  This configuration mutation is local DEV state only; the assertion root cause
  remains UNKNOWN if it recurs.

## Completion verification

- 2026-09-22 — The human accepted the Phase 2.1 in-game QA. Current DEV DB
  queries confirm all 12 quest rows, five custom item rows, and seven custom
  loot rows remain applied. The tracked Item.dbc dry run confirms all five
  mapped records `92060`–`92064` exist.
- The local authserver is running. Worldserver is currently stopped after the
  separately recorded runtime assertion; this is not attributed to this quest
  feature and does not alter accepted in-game QA. Effective local DEV
  `Console.Enable` remains `0`.
- The implementation commit `4fb340a` and separate harness-policy commit
  `72d55e5` were created externally by the human. The agent did not stage,
  commit, or publish. The only remaining task-owned working-tree change is the
  client-assets documentation addition recorded by final review.
