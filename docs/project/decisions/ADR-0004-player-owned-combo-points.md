# ADR-0004: Player-owned combo points

Status: Accepted
Date: 2026-09-21

## Context

AzerothCore's combo-point system stores points on the caster `Unit` but binds
their lifetime and spell validation to a raw target pointer (`m_comboTarget`).
Switching targets while building combo points resets the pool, and the death,
despawn, or evade of the original target clears it. This matches WotLK 3.3.5
retail behavior, where combo points belong to the target.

The project wants player-controlled Rogues and Druids to use a player-owned
model: points belong to the player, persist across target switches, and can be
consumed by a finisher on a different target.

## Decision

Implement player-owned combo points as a minimal AzerothCore core patch scoped
to player Rogues and player Druids.

Scoping rule: a unit owns its combo points in the player-owned sense only when
`IsPlayer() && (IsClass(CLASS_ROGUE) || IsClass(CLASS_DRUID))` is true on the
**pool owner** (the unit that holds, queries, or gains the points). All
behavioral changes are gated by this rule.

The gate is class-based rather than form-based. Combo-point ownership is a
resource-property decision; Cat Form and other requirements continue to be
enforced by ordinary spell and form validation.

Behavioral rules:

1. **Pool accumulation on target switch.** When a Rogue or Druid generates
   points on a new target, the points add to the existing pool instead of
   replacing it, subject to the existing cap of 5.
2. **Finisher validation.** `GetComboPoints(Unit const*)` returns the player's
   current pool regardless of whether the queried unit is the original combo
   target. This allows finishers on any valid target to consume stored points.
3. **Target loss does not clear points.** When a former target dies,
   despawns, or evades, the player's `m_comboTarget` pointer is unlinked but
   the point count is preserved.
4. **Display follows selection.** `SMSG_UPDATE_COMBO_POINTS` is sent with the
   player's current selection GUID (`UNIT_FIELD_TARGET`), and the packet is
   re-sent on every `CMSG_SET_SELECTION`. This is the closest correct behavior
   achievable without a client-side modification.
5. **Non-player users unchanged.** Warrior Overpower reactive token, Hunter pet
   Wolverine Bite reactive token, NPC combo counters, and vehicle drakes retain
   their target-bound semantics.
6. **Own death/logout/map-change still clears.** The patch only protects
   points against loss of the *former target*, not against the player's own
   death, logout, or map change.
7. **Shapeshift behavior remains WotLK.** Leaving or re-entering Cat Form does
   not introduce modern form-specific combo-point rules; existing WotLK
   behavior is preserved.

## Alternatives considered

### Generic player-owned combo points for all users

Rejected: it would break the Warrior Overpower / Hunter pet Wolverine Bite
reactive tokens, which rely on target-bound clearing, and would incorrectly
modernize NPC and vehicle mechanics.

### Form-based gating for Druids (only in Cat Form)

Rejected: combo-point ownership is a resource-property decision. Keying it on
current form could create inconsistent behavior when points are held across
form changes and would not simplify any caller. Ordinary spell requirements
already enforce whether an ability can generate or spend points.

### Module-only implementation

Rejected: `Unit::AddComboPoints`, `Unit::GetComboPoints`, and the finisher
check in `Spell::CheckCast` are not virtual and have no interception hooks. A
module could not safely change cast validation, consumption, or target-death
behavior without polling, and the plan forbids periodic polling.

### Core hook + module

Rejected: it would require adding hook call sites in the same functions that
must change anyway, producing a larger, harder-to-maintain artifact with no
additional consumer.

### Database-only customization

Rejected: combo-point ownership is implemented entirely in C++ state machines
and packet composition; no DBC or world DB field can relocate ownership.

## Consequences

### Positive

- Rogue and Feral Druid target switching behave as requested without changing
  unrelated mechanics.
- The change remains small and localized to `Unit` and one opcode handler.
- No database migration or client patch is required.

### Negative / trade-offs

- Intentional non-Blizzlike deviation for Rogues and Feral Druids.
- PvP balance changes: a Rogue or Feral Druid can build points on one target
  and finish another.
- The 3.3.5 client displays combo points on a specific unit; when the player
  deselects everything, the points exist server-side but may not render until
  a new target is selected.
- Upstream changes to combo-point symbols in `Unit.h`/`Unit.cpp` or
  `MiscHandler.cpp` will require patch maintenance.

## mod-playerbots compatibility

No module source changes are required to compile or run. The only target-gated
bot consumer (`mod-playerbots/src/Ai/Base/Value/StatsValues.cpp:134-147`)
returns 0 after a target switch until the first builder updates `m_comboTarget`;
this is already strictly better than the current reset behavior, and the API
remains compatible.

Because the module repository is read-only for this task, a targeted one-line
update was not applied. If the module is unblocked in the future, the
following change removes the stale target-bound assumption:

```cpp
if (!target || (target->GetGUID() != bot->GetComboTargetGUID() &&
                !bot->HasPlayerOwnedComboPoints()))
    return 0;
```

Other bot consumers use the no-argument `GetComboPoints()` or are creature
vehicles outside the player-owned scope.

## Validation notes

A reported Feral Druid regression (combo points not carrying to a new target)
was traced to a stale worldserver process still running the pre-Druid binary,
not to a source-code defect. After terminating the stale process and starting
a fresh instance with the current patch, both Rogue and Feral Druid target
switching behaved as designed.

## References

- `patches/core/player-owned-combo-points.patch`
- `patches/core/README.md`
- Completed plan: `~/azerothcore-setup/plans/completed/player-owned-combo-points.PLAN.md`
- Upstream context: AzerothCore PR #9816 introduced the current Unit-level
  target-owned combo-point system.
