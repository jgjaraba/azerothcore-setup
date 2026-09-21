# Player-owned combo points — core patch

## What this changes

This patch relocates combo-point ownership from the enemy target to the player
for player-controlled Rogues and Druids in AzerothCore.

Behavior after applying:

- Combo points generated on target A are preserved when the player selects
  target B.
- Additional points generated on target B add to the same pool (capped at the
  existing WotLK maximum of 5).
- A valid Rogue or Feral finisher used on target B consumes the existing pool.
- Changing selection does not create, destroy, or duplicate combo points.
- Death, despawn, or evade of a former target does not remove the player's
  points.
- Combo points are displayed on the player's current target, limited by what
  the 3.3.5 client protocol supports.

Non-player combo-point users (Warrior Overpower reactive token, Hunter pet
Wolverine Bite, vehicle drakes, NPCs) keep their existing target-bound
semantics.

## Files changed in AzerothCore

- `src/server/game/Entities/Unit/Unit.h`
- `src/server/game/Entities/Unit/Unit.cpp`
- `src/server/game/Handlers/MiscHandler.cpp`

Key symbols:

- `Unit::HasPlayerOwnedComboPoints()` — gate for player Rogues and Druids.
- `Unit::GetComboPoints(Unit const*)` — bypasses target check for player-owned
  users.
- `Unit::AddComboPoints(Unit*, int8)` — accumulates on target switch for
  player-owned users.
- `Unit::ClearComboPoints()` — clears even when no target is present.
- `Unit::OnComboTargetRemoved()` — new lifetime handler.
- `Unit::ClearComboPointHolders()` — uses `OnComboTargetRemoved()`.
- `Unit::SendComboPoints()` — displays points on current selection for
  player-owned users.
- `WorldSession::HandleSetSelectionOpcode()` — re-sends combo points on
  selection change for player-owned users.

## Base commit

This patch was authored against:

```
b4bbae96d3ff9fd8b85bede269cfba8ad28aad2a
```

Branch: `feat/rogue-player-owned-combo-points`

## Check before applying

```bash
~/azerothcore-setup/scripts/apply-core-patches.sh --validate
```

Possible outcomes:

- `APPLIES CLEANLY` — patch is not present and can be applied.
- `ALREADY APPLIED` — patch contents are already in the working tree.
- `CONFLICT` — upstream changes overlap with the patch; manual resolution is
  required.

## Apply to a clean compatible tree

```bash
# Ensure AzerothCore is at or near the base commit.
cd /home/dev/azerothcore

# Optional: verify the patch applies without touching the tree.
~/azerothcore-setup/scripts/apply-core-patches.sh --validate

# Apply.
~/azerothcore-setup/scripts/apply-core-patches.sh
```

After applying, rebuild and reinstall worldserver (AzerothCore modules are
statically linked, so a binary rebuild is required):

```bash
cd /home/dev/azerothcore/build
cmake --build . --config RelWithDebInfo --target install -j$(nproc)
```

Then restart authserver and worldserver.

## Identify an upstream conflict

Run the validate command after updating AzerothCore:

```bash
~/azerothcore-setup/scripts/apply-core-patches.sh --validate
```

If a patch reports `CONFLICT`, inspect the conflict with:

```bash
git -C /home/dev/azerothcore apply --check \
    ~/azerothcore-setup/patches/core/player-owned-combo-points.patch
```

Resolve the conflict in a feature branch, regenerate the patch, and update
this README's base commit.

## Remove / revert

```bash
cd /home/dev/azerothcore

git apply --reverse \
    ~/azerothcore-setup/patches/core/player-owned-combo-points.patch
```

If the patch no longer applies in reverse, resolve the conflict manually or
restore the three source files from a known clean commit after preserving any
unrelated local changes.

Then rebuild and reinstall worldserver, and restart the servers.

## Validate after applying

1. Run the core codestyle linter:

   ```bash
   python3 /home/dev/azerothcore/apps/codestyle/codestyle-cpp.py
   ```

2. Build and install worldserver.

3. Start authserver/worldserver and check for startup errors.

4. In-game manual test matrices (see the completed execution plan):

   **Rogue:**
   - 1 point on A → select B
   - 3 points on A → select B
   - points on A → generate more on B
   - points on A → finisher on B
   - A → B → A switching
   - former target dies
   - former target evades/despawns
   - clear selection → select new target
   - reach combo-point cap across multiple targets
   - finisher consumes all expected points
   - Premeditation / retained-point behavior
   - Rogue death/reset behavior
   - mod-playerbots Rogue behavior

   **Feral Druid:**
   - 1 point on A → select B
   - 3 points on A → select B
   - points on A → generate more on B
   - points on A → Feral finisher on B
   - A → B → A switching
   - former target dies
   - former target evades/despawns
   - clear selection → select new target
   - reach combo-point cap across multiple targets
   - finisher consumes all expected points
   - leave Cat Form → re-enter Cat Form
   - Cat → other form → Cat
   - Druid death/resurrection
   - retained-point talent/effect behavior
   - explicit-target ability/macro if applicable
   - mod-playerbots Feral behavior

## Regenerate this patch

After resolving conflicts or adjusting the implementation in AzerothCore:

```bash
cd /home/dev/azerothcore
git diff -- \
    src/server/game/Entities/Unit/Unit.h \
    src/server/game/Entities/Unit/Unit.cpp \
    src/server/game/Handlers/MiscHandler.cpp \
    > ~/azerothcore-setup/patches/core/player-owned-combo-points.patch
```

Update the base commit in this README and in
`scripts/apply-core-patches.sh` (`EXPECTED_BASE`).

## Upstream-update sensitivity

High-touch files:

- `src/server/game/Entities/Unit/Unit.cpp` — combo-point lifecycle.
- `src/server/game/Entities/Unit/Unit.h` — combo-point API.
- `src/server/game/Handlers/MiscHandler.cpp` — selection opcode.

Any upstream change that touches `m_comboTarget`, `m_comboPoints`,
`AddComboPoints`, `ClearComboPoints`, `SendComboPoints`,
`ClearComboPointHolders`, or `HandleSetSelectionOpcode` can conflict.

## Notes

- This is an intentional non-Blizzlike customization. WotLK 3.3.5 combo points
  are target-bound.
- No database schema or data change is required.
- No client patch (MPQ) is required; display uses the existing
  `SMSG_UPDATE_COMBO_POINTS` opcode.
- mod-playerbots does not require source changes to compile, but its
  `StatsValues.cpp:143` target-match check means Rogue and Feral bots will
  report zero combo points on a freshly switched target until the first builder
  lands and updates `m_comboTarget`. This is documented in ADR-0004. A one-line
  module patch (`target->GetGUID() != bot->GetComboTargetGUID() &&
  !bot->HasPlayerOwnedComboPoints()`) would remove the target-bound assumption
  if the module is ever unblocked for editing.
- The ownership gate is class-based (`CLASS_ROGUE` or `CLASS_DRUID`) rather
  than form-based, because combo-point ownership is a resource-property
  decision while Cat Form and other requirements continue to be enforced by
  ordinary spell and form validation.
