# Durable learnings

Verified operational and engineering findings that are easy to get wrong, cost
real debugging time, or are invisible in the source tree. Each entry states the
symptom, the cause and the check that proves it.

Add an entry when a finding is verified and would save a future investigation.
Do not add an entry for a transient error, a one-off typo or anything the
repositories or the machine already answer directly.

## Runtime and lifecycle

### `status.sh` exits nonzero when the servers are stopped

`scripts/status.sh` returns a nonzero exit status to report "stopped". A
nonzero result from that script is its stopped-state answer, not a script
failure. Do not treat it as an error or retry it.

### A worldserver started outside the lifecycle scripts is invisible to them

A stale `worldserver` process that was not launched by `scripts/start.sh`
keeps port `8085`, so a subsequent `start.sh` "succeeds" while the old process
still serves clients. The result is behaviour that does not match the current
source, no output from new instrumentation, and a misleading conclusion that a
patch is broken.

Always confirm runtime identity from the live system, not from the script:
current PID and start time, listening sockets on `3724`/`8085`, and log output
produced by the current invocation. A historical line in an append-only log is
not evidence about the process that is running now.

### A worldserver assertion is not attributable without a lookup type

`ASSERT_NOTNULL_IMPL: LookupEntry(id)` names neither the lookup type nor the ID.
It cannot be attributed to custom DBC or SQL data from the message alone.
Bounded checks that *did* clear a suspected custom cause: the installed
`CreatureDisplayInfo.dbc` contained the custom display, its `CreatureModelData`
model existed, and every display ID referenced by `creature_template_model` was
present in the installed display DBC. Reach for that style of evidence instead
of guessing.

### `Console.Enable = 1` creates an unbounded log in a managed DEV run

With the effective DEV `Console.Enable = 1`, a noninteractive managed
`worldserver` keeps receiving the `AC>` prompt and its console output file grew
to ~1.8 GiB. Keep the effective DEV value at `0` for managed runs. After fixing
it, confirm the log stops growing rather than assuming the process is healthy.

### Verbose entity logging is not a debugging aid for large runs

`Logger.entities.unit=4` on a populated world produced ~12 GiB of log, almost
entirely from one high-frequency path, and buried the player events the
investigation was about. Prefer targeted instrumentation with a bounded
lifetime, and truncate the log after changing log levels.

### `acore_auth.realmlist.flag` must be `0` for a usable DEV realm

A non-zero flag (`2`, `3`) leaves authserver unable to serve the local realm:
startup fails or the realm immediately goes offline. The DEV realm is
`AzerothCore DEV` on `127.0.0.1:8085`. The flag has been observed reverting to
`3` between restarts more than once, so check it whenever authserver will not
stay up rather than assuming the previous correction persisted.

## Git and the DEV tree

### Branch before editing, in both repositories

The two repositories have different base branches: `/home/dev/azerothcore`
uses `master`, `/home/dev/azerothcore-setup` uses `main` and has no `master`
branch at all. Create and switch a feature branch in each repository you will
modify before editing. This is ordinary setup, not an approval gate — see
[`decisions/ADR-0005-minimal-autonomous-harness.md`](decisions/ADR-0005-minimal-autonomous-harness.md).

## AzerothCore internals worth knowing

### Combo points are target-bound in upstream AzerothCore

Points live on the caster `Unit` but their lifetime is gated by a raw
`Unit* m_comboTarget`. `AddComboPoints` *replaces* the pool when the target
changes, and target death, despawn or evade clears it through
`ClearComboPointHolders`. Upstream introduced this in PR #9816 to match 3.3.5
retail, where combo points belong to the target. Any player-owned behavior must
be an explicit core patch; no database, DBC or hook can express it. See
[`decisions/ADR-0004-player-owned-combo-points.md`](decisions/ADR-0004-player-owned-combo-points.md).

### `mod-playerbots` gates its "combo" stat on the combo target

`modules/mod-playerbots/src/Ai/Base/Value/StatsValues.cpp` returns `0` unless
`target->GetGUID() == bot->GetComboTargetGUID()`. After a player-owned
combo-point change this makes bot combo-point statistics read `0` between a
target switch and the next builder. It is a documented limitation, not a
regression, and the fix is one condition.

### Static module SQL and database structure are not symmetric

`mod-morphsummon` defines `601072`, `61072`–`61074` and its character table
upstream, while the project's appearance-unlock work adds its own tables, items
`91001`–`91079`, loot and gossip filtering in a local fork. Source and SQL must
be deployed together or the feature is silently absent.

### Playerbots reports "Unknown Playerbots Database Revision" from an empty table

`version_db_playerbots` is the revision table the module displays, while
`updates` is the applied-update record. An empty revision table produces that
message but does **not** prove that updates are missing. Compare update hashes
and files before concluding anything.

### Playerbots requires its own core fork

`mod-playerbots` and the Individual Progression / Character Services / Dungeon
Clear / MultiBot Bridge chain all expect a Grimfeather Playerbots fork, not
stock AzerothCore. An upstream AzerothCore update is a coordinated ecosystem
exercise, not a core-only upgrade. A module that previously compiled can stop
compiling after a module update; check the module revisions before diagnosing a
core build failure.

### AzerothCore codestyle scans the whole tree

`apps/codestyle/codestyle-cpp.py` reports pre-existing violations in untouched
core files. For a database-only or documentation change, an unrelated codestyle
failure is not a result of the change — say so explicitly instead of treating it
as a failure of the work. The SQL linter runs under `python3`; `python` may not
exist.

## Tooling

### `shellcheck` is not installed on this VM

Validate shell scripts with `bash -n` and by running them, and do not report a
missing `shellcheck` as a pending requirement.
