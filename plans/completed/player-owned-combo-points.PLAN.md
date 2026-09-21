# Task: Player-owned combo points

Status: completed
Created: 2026-09-21
Last updated: 2026-09-21

## Goal

Change AzerothCore combo-point ownership so that player-controlled Rogues and
Druids own their combo points rather than the enemy on which the points were
generated.

Desired semantics:

- Generating combo points on target A then selecting target B preserves the
  points.
- Generating additional points on target B adds to the same pool (subject to
  existing WotLK cap).
- A valid Rogue or Feral finisher on target B can consume the existing points.
- Changing targets must not reset, duplicate, or create per-target pools.
- Death/despawn/evade of a former target must not remove points.
- Client combo-point display must follow the current target as closely as the
  3.3.5 protocol allows.
- Non-player combo-point users (Warrior Overpower, Hunter pet Wolverine Bite,
  NPCs, vehicles) must keep current WotLK target-bound behavior.
- Existing Rogue and Druid spells/talents/mechanics that manipulate combo
  points must remain compatible.
- mod-playerbots must remain compatible.

## Scope

### Included

- AzerothCore core combo-point infrastructure changes required for player-owned
  semantics for player Rogues and Druids.
- Investigation of existing combo-point consumers and lifetime handling,
  including Feral-specific paths.
- Reproducible, update-safe customization artifact under azerothcore-setup.
- Build/install/runtime validation on the DEV VM.
- Static/code review and automated/manual test strategy.

### Excluded

- Client-side modifications.
- Generic modernization of non-player combo-point users.
- Changes to unrelated Rogue or Druid mechanics (coefficients, talents,
  energy/rage costs, miss behavior, stealth, shapeshift rules other than
  combo-point ownership itself, etc.).
- Production or remote systems.
- Automatic staging/commits/PRs.

## Baseline

- AzerothCore: `/home/dev/azerothcore`
  - Branch: `feat/rogue-player-owned-combo-points`
  - HEAD: `b4bbae96d3ff9fd8b85bede269cfba8ad28aad2a`
  - Working tree: clean
- azerothcore-setup: `/home/dev/azerothcore-setup`
  - Branch: `feat/rogue-player-owned-combo-points`
  - HEAD: `1f82872a28d5e59803316b315e11cabaa51ae572`
  - Working tree: clean
- mod-playerbots (read-only): `/home/dev/azerothcore/modules/mod-playerbots`
  - Branch: `master`
  - HEAD: `7bae1b5c` (manually updated during this task)
  - Working tree: clean
- mod-dungeon-clear (read-only): `/home/dev/azerothcore/modules/mod-dungeon-clear`
  - Branch: `master`
  - HEAD: `29c53fd` (manually updated during this task)
- mod-multibot-bridge (read-only): `/home/dev/azerothcore/modules/mod-multibot-bridge`
  - Branch: `main`
  - HEAD: `759c100` (manually updated during this task)
- Other modules present and enabled; see module directories for exact HEADs.
- Build/install present at `/home/dev/azerothcore/env/dist`.

## Constraints

- Smallest maintainable change.
- No database schema change expected.
- No periodic polling / OnPlayerUpdate target switching.
- No partial patch application.
- No unrelated working-tree changes.
- No branch/commit/push/PR actions by the agent.

## Research findings

Source investigation completed by ac-research.

### Ownership model today

Combo points live on the caster `Unit` but access/lifetime are gated by a raw
`Unit* m_comboTarget`:

- `src/server/game/Entities/Unit/Unit.h:2248-2250` — `Unit* m_comboTarget`,
  `int8 m_comboPoints`, `std::unordered_set<Unit*> m_ComboPointHolders`.
- `Unit.h:1020-1031` — public API.
- `Unit.cpp:12801-12825` — `AddComboPoints`: switching to a new target
  **resets** the pool to the new count (`m_comboPoints = count`).
- `Unit.cpp:12827-12842` — `ClearComboPoints`: zeroes points and unregisters
  holder; early-returns if `!m_comboTarget`.
- `Unit.cpp:12844-12880` — `SendComboPoints`: sends `SMSG_UPDATE_COMBO_POINTS`
  with `m_comboTarget` packed GUID (empty if null).
- `Unit.cpp:12882-12888` — `ClearComboPointHolders`: called when the target
  dies/despawns/evades; calls `ClearComboPoints()` on every holder.

### Spell interaction

- `Spell::CheckCast` at `Spell.cpp:7036-7053` blocks explicit-target finishers
  unless `GetComboPoints(m_targets.GetUnitTarget())` returns >0.
- `Spell::_handle_finish_phase` at `Spell.cpp:4394-4417` clears CP for finishers
  and then applies `AddComboPoints(m_comboTarget, m_comboPointGain)`.
- `SPELL_EFFECT_ADD_COMBO_POINTS` at `SpellEffects.cpp:4274-4287` binds gains
  to the spell's hit target.
- `SPELL_AURA_RETAIN_COMBO_POINTS` (Premeditation) at
  `SpellAuraEffects.cpp:5144-5158` already uses the no-target overload.

### Event handling

- Target death: `Unit::setDeathState` (`Unit.cpp:11093`) calls
  `ClearComboPointHolders()`.
- Target despawn/map-remove: `Unit::CleanupBeforeRemoveFromMap`
  (`Unit.cpp:12189-12190`).
- Target evade: `CreatureAI::_EnterEvadeMode` (`CreatureAI.cpp:405`).
- Player death: `Player::setDeathState` (`Player.cpp:1096-1097`) clears CP.
- Player logout/map-change: `Player::RemoveFromWorld` (`Player.cpp:1767-1768`).
- Duel end: `Player::DuelComplete` (`Player.cpp:6723-6740`) clears CP when the
  combo target is the opponent or opponent's pet.
- `CMSG_SET_SELECTION` / `Player::SetSelection`: **no combo-point interaction**
  today.

### Non-player combo-point users (must not be silently modernized)

- Warrior Overpower reactive token (`Unit.cpp:12403`).
- Hunter pet Wolverine Bite reactive token (`Unit.cpp:12411`).
- `boss_zuljin.cpp:185` NPC combo counter.
- EoE vehicle drakes (via `GetComboPoints(target)`).

A generic "player-owned" change would affect all of these; the change must be
scoped to player Rogues and Druids.

### mod-playerbots assumptions

- `modules/mod-playerbots/src/Ai/Base/Value/StatsValues.cpp:134-147`: the
  `"combo"` value returns 0 unless `target->GetGUID() ==
  bot->GetComboTargetGUID()`. This affects both Rogue and Feral bots under
  player-owned semantics.
- `DpsTargetValue.cpp:242-262` prefers the current combo target; mostly
  harmless but may be updated.
- Vehicle code in `EoEActions.cpp:371-407` uses target-qualified CP and must
  remain unchanged.

### Feral-specific findings

- Druid builders use the generic `SPELL_EFFECT_ADD_COMBO_POINTS` path and
  `AddComboPointGain()` (SpellEffects.cpp, Spell.cpp).
- Mangle (Cat) adds a combo point at `SpellEffects.cpp:3684`.
- Feral finishers (Rip, Ferocious Bite, Maim, Savage Roar) rely on core
  finishing-move validation in `Spell.cpp:7036-7053`.
- Rip scaling reads `GetComboPoints()` at `spell_druid.cpp:869`.
- Leaving or re-entering Cat Form does not currently clear combo points; no
  form-specific combo-point logic exists.
- No Druid script directly assumes `GetComboTargetGUID()` is authoritative.

### Client protocol

- `SMSG_UPDATE_COMBO_POINTS` carries `[packed target GUID][uint8 points]`.
- With no combo target the packet sends an empty packed GUID; whether the client
  still renders the points is unverified.
- Likely need to re-send on selection change so the client displays points on
  the current target.

## Decisions

### Approach

**Minimal AzerothCore core modification + durable core-patch artifact in
azerothcore-setup.**

Reasons alternatives were rejected:
- **Database-only:** impossible — the behavior is implemented in C++ state
  machines (`Unit::AddComboPoints`, `Spell::CheckCast`, target-death clearing,
  `SMSG_UPDATE_COMBO_POINTS`).
- **Existing scripting hooks:** none exist for combo-point add/query/clear/send.
- **Module-only:** `Unit` combo members/mutators are non-virtual and not
  interceptable; a module could not safely change cast validation/consumption
  or prevent target-death clearing without polling.
- **Core hook + module:** would add hook call sites in the same functions that
  must change anyway, producing a larger, harder-to-maintain artifact.

### Player-owned scope

`Unit::HasPlayerOwnedComboPoints()` returns `IsPlayer() &&
(IsClass(CLASS_ROGUE) || IsClass(CLASS_DRUID))`. All behavioral changes are
gated on the **pool owner** (the unit holding/querying/gaining points), never
on the target. The gate is class-based, not form-based, because combo-point
ownership is a resource-property decision while Cat Form and other
requirements continue to be enforced by ordinary spell/form validation.

This preserves target-bound semantics for Warrior Overpower, Hunter pet
Wolverine Bite, NPCs, and vehicles.

### Client display

`SMSG_UPDATE_COMBO_POINTS` carries `[packed target GUID][uint8 points]`. For
player-owned Rogues and Druids the display GUID is the current selection
(`UNIT_FIELD_TARGET`), and `HandleSetSelectionOpcode` re-sends the packet on
target change. This is the closest correct behavior achievable without client
modification.

### Target death/despawn/evade

All three removal paths funnel through `Unit::ClearComboPointHolders`.
`Unit::OnComboTargetRemoved()` keeps the pool for player-owned users while
unlinking the raw `m_comboTarget` pointer, preserving the existing symmetric
holder-set invariant and avoiding dangling pointers.

### Shapeshift / Cat Form

Leaving or re-entering Cat Form does not introduce modern form-specific
combo-point rules. Existing WotLK behavior is preserved: no form change
currently clears combo points.

### mod-playerbots

No module changes are required to compile or run. The target-gated bot
consumer (`StatsValues.cpp:140-147`) briefly reports 0 after a switch until
the first builder updates `m_comboTarget`; this is strictly better than the
current reset behavior. The task forbids module writes without explicit
unblock.

### Reproducibility

Core-patch mechanism under `patches/core/`:

- `patches/core/player-owned-combo-points.patch` — exact `git diff` produced
  from the task-owned core changes.
- `patches/core/README.md` — what it changes, pinned base commit, apply/remove/
  validate/rollback procedures, upstream-update sensitivity.
- `patches/core/manifest.txt` — ordered patch inventory.
- `scripts/apply-core-patches.sh` — manifest validation, base-commit warning,
  dry-run/check mode, apply with detection of already-applied / conflict /
  clean-apply states.

### ADRs

- `docs/project/decisions/ADR-0003-core-source-patches.md`
- `docs/project/decisions/ADR-0004-player-owned-combo-points.md` (revised from
  the Rogue-only version)


## Implementation

### AzerothCore core changes

Modified files:

- `src/server/game/Entities/Unit/Unit.h`
- `src/server/game/Entities/Unit/Unit.cpp`
- `src/server/game/Handlers/MiscHandler.cpp`

Changes:

1. `Unit::HasPlayerOwnedComboPoints()` — returns `IsPlayer() &&
   (IsClass(CLASS_ROGUE) || IsClass(CLASS_DRUID))`.
2. `Unit::GetComboPoints(Unit const*)` bypasses the target gate when the owner
   is a player Rogue or Druid.
3. `Unit::GetComboPoints(ObjectGuid const&)` also returns the pool for
   player-owned users when the GUID does not match the current combo target.
4. `Unit::AddComboPoints(Unit*, int8)` accumulates on target switch for
   player-owned users instead of resetting the pool.
5. `Unit::ClearComboPoints()` clears even when `m_comboTarget` is null for
   player-owned users, and guards the holder-unregister block.
6. `Unit::OnComboTargetRemoved()` — for player-owned users it unlinks the
   target pointer and keeps the pool; for others it calls `ClearComboPoints()`.
7. `Unit::ClearComboPointHolders()` calls `OnComboTargetRemoved()` instead of
   `ClearComboPoints()`.
8. `Unit::SendComboPoints()` uses the current selection (`UNIT_FIELD_TARGET`)
   as the display GUID for player-owned users.
9. `WorldSession::HandleSetSelectionOpcode()` re-sends combo points after
   selection change for player-owned users.

### azerothcore-setup reproducibility artifacts

- `patches/core/player-owned-combo-points.patch` — exact `git diff` of the
  core changes.
- `patches/core/manifest.txt` — ordered patch inventory.
- `patches/core/README.md` — what it changes, pinned base commit, apply/remove/
  validate/rollback procedures, upstream-update sensitivity.
- `scripts/apply-core-patches.sh` — manifest validation, dry-run/check mode,
  apply with detection of already-applied / conflict / clean-apply states.
- `docs/project/decisions/ADR-0003-core-source-patches.md` — decision to
  introduce the core-patch mechanism.
- `docs/project/decisions/ADR-0004-player-owned-combo-points.md` — decision
  on player-owned combo points for Rogues and Druids.

## DEV mutation log

1. Regenerated environment state with `refresh-environment.sh`.
2. Created active execution plan under `plans/active/`.
3. Implemented core changes in AzerothCore working tree.
4. Generated `patches/core/rogue-player-owned-combo-points.patch` from the
   working-tree diff.
5. Created manifest, README, apply script, and ADRs in azerothcore-setup.
6. Reconfigured CMake to disable modules with unrelated compile failures:
   `mod-playerbots`, `mod-dungeon-clear`, `mod-multibot-bridge`.
7. Built and installed AzerothCore (`cmake --build . --target install`).
8. Restarted authserver/worldserver with the new binaries.
9. Fixed pre-existing DEV `acore_auth.realmlist` flag (`2` → `0`) so
   authserver stays running; this was blocking client login and was unrelated
   to the combo-point change.
10. Extended `HasPlayerOwnedComboPoints()` to include `CLASS_DRUID`.
11. Regenerated and renamed the core patch to
    `patches/core/player-owned-combo-points.patch`.
12. Renamed/revised ADR-0004 to
    `docs/project/decisions/ADR-0004-player-owned-combo-points.md`.
13. Rebuilt and reinstalled with all modules enabled.
14. Restarted authserver/worldserver.
15. Final `ac-review` flagged:
    - braces around single-statement branches in `Unit.cpp` and `MiscHandler.cpp`;
    - ADR-0004 referenced the old Rogue-only plan filename;
    - README removal procedure used `git checkout --` and could discard unrelated
      work;
    - playerbots remains target-bound semantically (documented);
    - duel cleanup retains target-provenance semantics (acceptable);
    - reproducibility records did not pin the manually updated module commits.
16. Fixed the three confirmed defects:
    - removed unnecessary braces in `Unit.cpp` and `MiscHandler.cpp`;
    - corrected ADR-0004 plan filename reference;
    - revised README removal procedure to use `git apply --reverse` first, with
      `git checkout --` only as a fallback.
17. Regenerated `player-owned-combo-points.patch` from the updated diff.
18. Rebuilt and reinstalled; restart succeeded with both servers running.
19. Fixed `acore_auth.realmlist.flag` back to `0` after it was reset to `3`
    (offline/version-mismatch) between restarts.

## Validation

### Static / compatibility validation

- Ran `python3 apps/codestyle/codestyle-cpp.py`; no new violations in changed
  files (all reported issues are pre-existing).
- Verified patch matches working-tree diff.
- Verified `apply-core-patches.sh --validate` detects states correctly:
  - after revert: `APPLIES CLEANLY`;
  - after apply: `ALREADY APPLIED`.
- Final `ac-review` confirmed the implementation is correct; identified defects
  were addressed.

### Build/install/runtime validation

- Initial full build failed because of pre-existing, unrelated module compile
  errors in `mod-playerbots`, `mod-dungeon-clear`, and `mod-multibot-bridge`
  at the current module commits.
- Reconfigured CMake to disable those three broken modules and verified the
  core build.
- After the user manually updated the module repositories, re-enabled all three
  modules in CMake:
  `-DMODULE_MOD-PLAYERBOTS=default -DMODULE_MOD-DUNGEON-CLEAR=default
  -DMODULE_MOD-MULTIBOT-BRIDGE=default`.
- Full `cmake --build . --target install` succeeded with all modules enabled.
- Restarted authserver/worldserver with the new binaries.
- Worldserver log reports `>> 100 random bot accounts with 1000 characters
  available` and `mod-playerbots initialized`.
- Fixed `acore_auth.realmlist.flag` from `2` to `0` so authserver stays
  running; note the flag was later observed reset to `3` and corrected again.
- Both servers report `running`; worldserver reached the `AC>` prompt with no
  startup errors related to the patch.
- Final incremental rebuild (after brace/style fixes) succeeded and installed.

### Independent review

Invoked `ac-review` three times. Confirmed findings addressed:
1. Patch installer now aborts immediately on the first failed patch
   (`scripts/apply-core-patches.sh`).
2. Inline functions in `Unit.h` reformatted to stay within the 120-column
   limit.
3. mod-playerbots semantic limitation documented; no module changes possible
   because module repositories are read-only for this task.
4. Removed braces around single-statement branches in `Unit.cpp` and
   `MiscHandler.cpp`.
5. Corrected ADR-0004 plan filename reference.
6. Revised README removal procedure to use reverse patch application and removed
   the `git checkout --` fallback that could discard unrelated work.
7. Recorded manually updated module HEADs in this plan for reproducibility.
8. Converted `scripts/apply-core-patches.sh` to two-space indentation and
   validated its Bash syntax and `--validate` behavior.

Deliberately deferred review findings:
- mod-playerbots still treats points as target-bound until a builder lands on
  the new target; module source was outside the writable scope and the
  limitation is documented in ADR-0004 and the patch README.
- `Player::DuelComplete()` retains last-target cleanup semantics; changing that
  policy was outside the requested ownership scope.
- The installer applies a multi-patch manifest one patch at a time. The current
  one-patch manifest is atomic; a future multi-patch transaction preflight is
  deferred as outside this task.

### Gameplay validation

- Rogue manual test matrix: PASS (completed by user before scope expansion).
- Feral Druid manual test matrix: PASS (completed by user against the fresh
  worldserver process; points carry to new targets and accumulate correctly).
- Automated gameplay testing is not available in the existing infrastructure.

## Feral target-switch regression diagnosis (resolved)

Reported symptom: Feral Druid combo points reset/disappear when switching targets.

### Phase 1 static inspection

Target-switch path:
- `WorldSession::HandleSetSelectionOpcode` reads the new selection GUID, calls
  `Player::SetSelection`, then calls `SendComboPoints()` for player-owned users.
- `Player::SetSelection` only updates `UNIT_FIELD_TARGET`; it does not touch
  combo points.
- No Druid-only or Cat-Form-specific combo-point clearing was found in spell
  scripts, aura handlers, or shapeshift code.
- For a player-owned user, `GetComboPoints(target)` returns the pool regardless
  of whether `target` matches `m_comboTarget`, so finishers should validate on
  the new target.

Preliminary classification: likely **Case B** (server-side pool preserved, client
synchronization/display issue), but runtime evidence is required to confirm.

### Phase 2 path inventory

All combo-point clear/reset paths identified:
- `Spell::_handle_finish_phase` — clears points when `m_needComboPoints` (finisher
  consumption), then re-adds any effect gain.
- `Player::setDeathState` — player death.
- `Player::RemoveFromWorld` — logout/map-change.
- `Player::DuelComplete` — duel cleanup against opponent/opponent pet.
- `Unit::CleanupBeforeRemoveFromMap` — unit deletion.
- `Unit::ClearAllReactives` / `Unit::UpdateReactives` — Warrior Overpower /
  Hunter pet Wolverine Bite reactive tokens only.
- `Unit::OnComboTargetRemoved` — target death/despawn/evade; keeps pool for
  player-owned users.

None of these should fire on a simple target switch for a Druid.

### Phase 3 diagnostic instrumentation

Temporary `CP-DIAG` logging added to:
- `WorldSession::HandleSetSelectionOpcode` — selection change request, state
  before `SetSelection`.
- `Unit::AddComboPoints` — entry/exit with target, count, and before/after pool.
- `Unit::ClearComboPoints` — entry with class/form/pool/target and player-owned
  flag.
- `Unit::OnComboTargetRemoved` — entry.
- `Unit::SendComboPoints` — packet target GUID and point count.
- All `ClearComboPoints` call sites labeled with caller identity.

Log categories enabled in `worldserver.conf`:
- `Logger.entities.unit=4,Console Server`
- `Logger.network=4,Console Server`
- `Logger.spells=4,Console Server`

DEV server rebuilt, installed, and restarted with instrumentation.
20. Log file had grown to 12 GB, almost entirely `CleanupBeforeRemoveFromMap`
    CP-DIAG lines; removed that source of spam, promoted remaining CP-DIAG
    logs to `LOG_ERROR`, and truncated the log so player events are visible.
21. `acore_auth.realmlist.flag` observed reset to `3` again; corrected to `0`
    and servers restarted.
22. **Critical discovery:** a stale worldserver process (pid 30743, started at
    12:57) was still running and serving client connections. The stop/restart
    cycle had started new worldserver instances, but the old process held port
    8085 and was never killed because it was launched outside the tracked
    lifecycle scripts. The user's client was connecting to this stale process,
    which explains why:
    - Feral Druid behavior did not match the current source;
    - CP-DIAG instrumentation produced no output;
    - Rogue appeared to work (stale process had the Rogue-only version of the
      patch).
23. Killed the stale worldserver with SIGKILL and started a fresh instance via
    the tracked lifecycle script. Fresh process is pid 62255.
24. User confirmed Feral Druid combo points carry to new targets and accumulate
    correctly on the fresh worldserver process.
25. Removed all temporary CP-DIAG instrumentation from Unit.cpp, MiscHandler.cpp,
    Spell.cpp, and Player.cpp.
26. Reverted temporary logger-category changes in `worldserver.conf`.
27. Regenerated `patches/core/player-owned-combo-points.patch` from the final
    working-tree diff.
28. `apply-core-patches.sh --validate` reports `ALREADY APPLIED`.
29. Codestyle check on changed files: no new violations.
30. Rebuilt and reinstalled; restarted authserver/worldserver with the clean
    binary. New worldserver pid is 65632.
31. Updated ADR-0004 with a validation note explaining the stale-process root
    cause of the reported regression.
32. Final `ac-review` requested fixes:
    - Removed the `git checkout --` fallback from `patches/core/README.md`.
    - Reconciled Feral test status in the active plan (now marked PASS).
    - Converted `scripts/apply-core-patches.sh` indentation from 4 spaces to
      2 spaces to match project shell-file conventions.

### Phase 4/5/6/7/8

Completed. The implementation is functionally correct for both Rogue and Feral
Druid. The reported regression was caused by a stale worldserver process, not a
source defect. The only remaining open item is the recurring
`acore_auth.realmlist.flag` reset to `3`, which is unrelated to combo points.

## Open issues

- [x] Complete combo-point source investigation (Rogue and Feral).
- [x] Decide between module-only / core-change / patch approach.
- [x] Confirm 3.3.5 client protocol limits for combo-point display at runtime
      for Feral Druids (confirmed working by user against fresh server).
- [x] mod-playerbots compatibility impact identified and documented.
- [x] Feral Druid manual gameplay test (completed by user).
- [ ] Determine why `acore_auth.realmlist.flag` resets to `3` between restarts
      and decide whether to fix or monitor (unrelated to combo points).
- [x] Diagnose and fix Feral Druid target-switch combo-point regression (root
      cause was a stale worldserver process, not source code).

## Playerbots investigation (resolved)

Observation: no playerbots spawned in the world.

Root cause: `mod-playerbots` was disabled in the CMake configuration because it
failed to compile at its previous commit (`b6696bdbd`) due to an undeclared
`PlayerbotsDatabase` identifier.

Resolution: the user manually updated the module repositories. After
re-enabling the three modules in CMake, the build succeeded and installed with
all modules loaded.

Current state:
- `MODULE_MOD-PLAYERBOTS=default`
- `MODULE_MOD-DUNGEON-CLEAR=default`
- `MODULE_MOD-MULTIBOT-BRIDGE=default`
- Worldserver log reports `>> 100 random bot accounts with 1000 characters
  available` and `mod-playerbots initialized`.
- Both authserver and worldserver are running.
- `acore_auth.realmlist.flag` was reset to `3` (offline/version-mismatch)
  between restarts and corrected back to `0`; cause under investigation.

## Next exact action

None. Task is complete and ready for human review. The unrelated
`acore_auth.realmlist.flag` reset remains documented for later investigation.
