# Forsaken Paladin class quests

Status: implemented and human in-game validated (Phase 2.1). Client patch-Z
packaging and deployment of the item records remain a human release
responsibility.

## Design contract

- Both chains are Undead Paladin-only (`AllowableRaces=16`,
  `AllowableClasses=2`) normal Paladin-class quests (`QuestSortID=-141`), with no
  repeatability, reputation, honor, title, talent, mail, currency, or time limit.
- The level-12 Redemption chain is `91010`–`91016`; the independent level-20
  weapon chain is `91020`–`91024`. Reserved IDs are all used because each step
  changes location, objective, or consequence; none is filler.
- The Ashen Hand is only a quiet informal name for a few Forsaken
  practitioners, never an organization, rank, faction, or hidden history.
- No Ambermill, Ivar Patch, Springvale, custom fallen target, resurrection
  encounter, event/controller, SmartAI, Melrache/bodyguard/quest-372 change,
  Individual Progression change, Playerbots change, module, or core change.
- Custom items are project-owned, modest materials recovered from existing
  sources. Their significance comes from Lordaeron's surviving places, not from
  invented relic lore.
- Ivar Patch was removed from the route because its kill objective duplicated the
  canonical `429 → 430 → 425` chain and no distinct ordinary alternative was
  evidenced.

## Ownership

- `data/sql/custom/db_world/forsaken_paladin.sql` is the sole canonical owner of
  Undead Paladin creation data, outfits, trainers, models, equipment, locales,
  addons and exact trainer spawns. Treat it as a frozen baseline.
- `data/sql/custom/db_world/forsaken_paladin_quests.sql` owns the quest chains,
  their relations, locales, custom loot rows, conditions and quest-item
  registrations. It is listed in `manifest.txt` immediately after the baseline.
- `dbc/forsaken_paladin_item_dbc_mapping.csv` records which existing Item.dbc
  record each custom item is cloned from. `scripts/item_dbc_tool.py` generates
  the server `Item.dbc` records; tracked `dbc/Item.dbc` is the result.

The authoritative enUS and esES quest text, rewards and relations are the SQL
itself. This document records the design contract and intent; it deliberately
does not duplicate the field text, so the two cannot drift apart.

## Item allocation and deployment

| ID | Item enUS | Item esES | Role |
|---:|---|---|---|
| 92060 | Ravenclaw Counterweight | Contrapeso Corvozarpa | Fenris component |
| 92061 | Agamand Weapon Haft | Mango de arma Agamand | Agamand component |
| 92062 | Durnholde Forged Iron | Hierro forjado de Durnholde | Durnholde component |
| 92063 | Rot Hide Binding | Atadura Putrepellejo | Rot Hide component |
| 92064 | Lordaeron's Vigil | Vigilia de Lordaeron | final weapon |

`92060`–`92063` are normal-quality, non-equippable, non-sellable, stack-one
quest items cloned from `7309`, retaining its existing icon/display. `92064` is
a bind-on-pickup, rare two-handed mace cloned field-for-field for gameplay from
Verigan's Fist `6953`: damage 65–99, speed 3.20, +7 Stamina, +12 Spirit, +6
Intellect, and no new effect. It uses provisional existing DisplayID `13466`.
The display is a human visual choice, not a readiness blocker.

| DBC | Records | Server | Regular patch-Z | HD patch-Z | Reason |
|---|---|---|---|---|---|
| Item.dbc | 92060–92063 cloned from 7309; 92064 from 6953 | required | required | required | client/server item identity and display contract |
| Other DBCs | none | n/a | n/a | n/a | existing NPCs, objects, spells and display are reused |

The five `Item.dbc` records must exist in the server DBC **and** in both client
patch-Z variants, and must be added to the existing custom records rather than
replacing them.

## Technical and group-loot contract

Each component is a project-owned additive loot row: `Chance=100`,
`QuestRequired=1`, `LootMode=1`, `GroupId=0`, `MinCount=MaxCount=1`. Canonical
rows are never deleted or changed. Each row has exactly one AND-grouped active
quest condition (`ElseGroup=0`, `ConditionTypeOrReference=9`, all unused values
zero):

| Component | Active quest | Condition key `(SourceType, SourceGroup, SourceEntry, quest)` |
|---:|---:|---|
| 92061 | 91021 | `(4, 4767, 92061, 91021)` — Agamand Weapon Rack loot |
| 92063 | 91021 | `(1, 1939/1940/1942/1943, 92063, 91021)` — Rot Hides |
| 92060 | 91022 | `(1, 1947, 92060, 91022)` — Thule Ravenclaw |
| 92062 | 91023 | `(1, 2261, 92062, 91023)` — Syndicate Watchman |

Quest-item registrations are `gameobject_questitem (105172, 92061)` and
`creature_questitem` rows for `(1939, 92063)`, `(1940, 92063)`, `(1942, 92063)`,
`(1943, 92063)`, `(1947, 92060)` and `(2261, 92062)`.

Core evaluates creature quest loot per eligible nearby group member; the
quest-loot-party hook makes normal-quality quest loot free-for-all. The Agamand
Weapon Rack has personal loot (`groupLootRules=0`), so each eligible player must
interact with it separately and wait for its ordinary respawn if necessary; one
opening does not award every group member. Playerbots may accompany humans as
ordinary group members; no bot AI or autonomous bot completion is required.

The four sources are classified SAFE for current ordinary-world use: DEV
contains ordinary phase-1 spawns and tracked Individual Progression zone data
has no target-specific phasing rule. If an effective source loot ID drifts, stop
and review rather than silently changing a creature template.

### Component provenance

| Item | Material and source | Why it belongs there |
|---|---|---|
| 92061 | Straight spare weapon haft from Agamand Weapon Rack 105172 | A weapon rack naturally holds replaceable hafts; the ruined estate keeps ordinary household arms. |
| 92063 | Cured Rot Hide strap from ordinary Rot Hide gear | Gnoll straps are mundane equipment, made foul by the region rather than mystical. |
| 92060 | Worked iron counterweight carried by Thule Ravenclaw 1947 | A compact piece of equipment is plausible on Thule; the iron is recovered, not celebrated. |
| 92062 | Sound forged iron from Syndicate Watchman 2261 at Durnholde | Watchmen plausibly carry refitted keep iron; the marks are burned off in the forge. |

## Redemption chain (`91010`–`91016`)

All quests have `QuestLevel=-1`, `MinLevel=12`, no money or item reward, and
their direct predecessor as `PrevQuestID`. `91010` has no predecessor. The
ordinary XP difficulties are 4, 5, 4, 4, 5, 4, and 6. Every quest uses ordinary
quest relations and talk, delivery, or shared kill credit.

| Quest | enUS / esES | Giver → receiver | Objective |
|---:|---|---|---|
| 91010 | A Handful of Ash / Un puñado de ceniza | Pancratius Ward 90211 → Abraham West 90210 | talk ender only |
| 91011 | A Kindness Without Witness / Bondad sin testigos | Abraham West → Caretaker Caice 2307 | Linen Cloth 2589 ×10, consumed |
| 91012 | What the Dead Still Need / Lo que aún necesitan los muertos | Caice → Abraham West | talk ender only |
| 91013 | The Measure of Mercy / La medida de la compasión | Abraham West → Magistrate Sevren 1499 | talk ender only |
| 91014 | The Light Without Pity / La Luz sin piedad | Magistrate Sevren | kill Scarlet Warrior 1535 ×8, then return |
| 91015 | A Report in Ash / Un informe en ceniza | Sevren → Abraham West | talk ender only |
| 91016 | The Light Does Not Spare Us / La Luz no nos da tregua | Abraham West | immediate same-NPC completion |

`91016` reproduces canonical Paladin quest `1788` reward semantics exactly:
`RewardXPDifficulty=6`, `RewardDisplaySpell=7328`, `RewardSpell=7329`, quest
flag `8` (`QUEST_FLAGS_SHARABLE`), no money, items, choices, reputation, honor
or mail. Resurrection is taught by that reward; there is no custom target and
no Symbol of Life encounter.

Narrative intent: Deathknell and Brill become a route from instruction to
service; the newly risen and their care are the first obligation rather than a
lecture; Brill's magistrate frames mercy as civil protection rather than
passivity; the reward teaches resurrection after care and defence.

## Level-20 weapon chain (`91020`–`91024`)

All quests have `QuestLevel=20`, `MinLevel=20`, ordinary quest relations, and no
money or spell reward. `91020` has no prerequisite; it must not require `91016`.
XP difficulties are 4, 5, 5, 5, and 6.

| Quest | enUS / esES | Giver → receiver | Objective |
|---:|---|---|---|
| 91020 | A Weapon of This Soil / Un arma de esta tierra | Abraham West → Basil Frye 4605 (War Quarter, Undercity) | talk |
| 91021 | Wood and Sinew / Madera y tendón | Basil Frye | 92061 from Agamand Weapon Rack 105172 + 92063 from any Rot Hide; both consumed |
| 91022 | The Raven's Weight / El peso del cuervo | Basil Frye | 92060 from Thule Ravenclaw 1947, Fenris Isle |
| 91023 | Iron in Captivity / Hierro cautivo | Basil Frye | 92062 from Syndicate Watchman 2261, Durnholde |
| 91024 | Lordaeron's Vigil / Vigilia de Lordaeron | Basil Frye | immediate completion, rewards exactly one 92064 |

`91024` is forge work, not a rite: no royal seal, no saint's name, no promise
that the Light considers the Forsaken worthy.

## Implementation conventions discovered while building this feature

These are reusable AzerothCore database findings, not feature trivia:

- **Talk-only quests must not create a creature objective.** A quest whose
  intent is travel/talk and that completes through its quest-ender relation
  (`quest_ender`) must have no `RequiredNpcOrGo` row. Adding a friendly-NPC
  objective makes the objective un-completable through ordinary talk.
- **A questgiver needs the quest flag.** Existing actors reused as quest givers
  (`2307`, `4605`, `90210`, `90211`) required `npcflag | 2`, applied so existing
  flags/services are preserved.
- **NPC dialogue and quest template text live in different tables.**
  `quest_template_locale` carries Title, Details, Objectives, EndText
  (`AreaDescription`), CompletedText (`QuestCompletionLog`) and `ObjectiveText1`.
  Progress text belongs in `quest_request_items_locale` and completion dialogue
  in `quest_offer_reward_locale`.
- **Deletion predicates must name the exact owned tuple.** A predicate that
  joins two columns can delete future project rows through a cross-product.
- **Re-applying the custom SQL must succeed.** Every implemented statement is
  idempotent so `apply-db-world.sh` can be run repeatedly; a second successful
  full application is part of the validation.
- **Gameplay parity is verified by column diff.** `92064` was checked against
  `6953` by querying every gameplay column: only `entry` and `name` differ.

## Validation expectations

- `scripts/apply-db-world.sh --validate` plus two successful full applications.
- Direct DEV queries confirming quest rows, relations, locales, custom loot rows,
  conditions and quest-item registrations.
- AzerothCore SQL codestyle (`apps/codestyle/codestyle-sql.py`).
- Server restart plus bounded inspection of recent `Server.log`/`Errors.log` for
  missing-questgiver or custom-data errors.
- Client patch-Z packaging and in-game behavior remain human steps: confirm only
  Undead Paladins receive the chains, confirm both locales, confirm the weapon's
  display and rendering in both client variants, and group-test the creature
  component loot plus the serial rack interaction.
