# Autonomous DEV Capability Smoke Test — Plan

## Task mode

`audit/read-only`, with the user-authorized disposable local DEV database write
probe described below.

## Scope

Verify local lifecycle status, local `acore_world` read/write capability using
the configured `azeroth-dev` login path, and existing build-environment
metadata. Do not modify source, Git state, server state, or external systems.

## Baseline

- `/home/dev/azerothcore`: branch `master`, HEAD
  `529b659668bcd8b1cfbf9acc44f40eb6ff830fe1`, clean.
- `/home/dev/azerothcore-setup`: branch `chore/autonomous-dev-agent`, HEAD
  `e9fd84578d151bec2911958b4a2b2743692add56`; 11 pre-existing modified harness
  paths. They will be preserved.
- No prior active execution plan exists.

## Execution plan

1. Run the tracked DEV status script without starting or stopping servers.
2. Use local MySQL login path `azeroth-dev` against `acore_world` to read its
   version row.
3. Create a unique disposable table, insert and read one sentinel row, drop
   it, and confirm it is absent. Record all database mutation SQL.
4. Inspect the existing CMake cache and installed paths only; do not configure
   or build.
5. Inspect final repository state and update this plan with exact results.

## DEV mutation log

- 2026-09-20: `refresh-environment.sh` regenerated the project generated
  environment inventory as required by startup protocol.
- 2026-09-20: User-authorized local `acore_world` write probe created, inserted
  into, read from, and dropped an initial dynamically named disposable table;
  absence was confirmed through `information_schema`. The generated table name
  and exact statements were not captured in the durable record; this is a
  documentation limitation, not remaining database state.
- 2026-09-20: Repeated the disposable write probe with
  `ac_agent_capability_smoke_20260920_153500`: `CREATE TABLE`; `INSERT` row
  `(1, 'autonomous-dev-capability-smoke')`; `SELECT`; `DROP TABLE`; and an
  `information_schema.tables` count of `0`. No test table or row remains.

## Results

- **PASS — lifecycle inspection:** `scripts/status.sh` identified both the
  managed `authserver` and `worldserver` as stopped. The script's nonzero exit
  is its documented stopped-server status, not an execution failure. Neither
  server was started or stopped.
- **PASS — local world version read:** the `azeroth-dev` MySQL login path read
  `acore_world.version`: `AzerothCore rev. 529b659668bc ... (master branch)
  (Unix, RelWithDebInfo, Static)` and `ACDB 335.17-dev`.
- **PASS — local database write and cleanup:** both disposable probes inserted
  and returned the expected sentinel row, then their `information_schema`
  absence checks returned `0` after dropping their tables.
- **PASS — build environment inspection:** existing `build/CMakeCache.txt`
  reports Unix Makefiles, Clang (`/usr/bin/clang` and `/usr/bin/clang++`),
  install prefix `/home/dev/azerothcore/env/dist`, static scripts/modules,
  `BUILD_TESTING=OFF`, and `TOOLS_BUILD=all`. Installed tools observed:
  CMake 3.31.6, Ninja 1.12.1, and Clang 19.1.7. No configuration or build was
  run.
- **NOT APPLICABLE — source changes, Git mutation, sudo, remote access:** none
  were required or performed.

## Initial database/build phase completion

The initial database/build checks completed. The later lifecycle validation
below completed the overall smoke test.

## Lifecycle validation (2026-09-20)

### Scope and baseline

- Task mode remains `audit/read-only`; the user explicitly authorized DEV
  lifecycle start/stop operations. Source and Git state were out of scope, as
  were agent database actions. A user-performed database correction was an
  explicit prerequisite for the final lifecycle validation and is recorded
  below.
- Baseline repositories remain `/home/dev/azerothcore` at
  `529b659668bcd8b1cfbf9acc44f40eb6ff830fe1` on `master` (clean) and
  `/home/dev/azerothcore-setup` at `e9fd84578d151bec2911958b4a2b2743692add56`
  on `chore/autonomous-dev-agent` (the same 11 pre-existing harness changes
  plus this untracked plan).
- **PASS — initial lifecycle inspection:** `scripts/status.sh` reported both
  managed servers stopped. Its nonzero exit is the script's stopped-state
  result, not a command failure. No stop operation was needed.

### Lifecycle mutation log

- 2026-09-20: `refresh-environment.sh` regenerated generated environment
  inventory as required by task startup protocol.
- 2026-09-20: Initial agent `scripts/start.sh` attempt failed while starting
  authserver and rolled back its managed process. Immediate `scripts/status.sh`
  confirmed both managed processes stopped. Historical append-only console logs
  were inspected, but their earlier shutdown lines are not evidence of the
  current PID state.
- 2026-09-20: The lifecycle scripts created or updated local runtime artifacts:
  runtime directory/lock, authserver console log, and managed PID-file state.
  `start.sh` invoked `ensure_runtime_config`, which can create adjacent
  configuration backups and rewrite `LogsDir` in the ignored DEV configuration;
  whether it changed either configuration file during this run was not captured
  and was not re-inspected. Worldserver did not start during this failed attempt.
- 2026-09-20: The smoke test discovered pre-existing local DEV realm state
  preventing authserver startup. The user manually applied the DEV-state
  correction below; it is not a source, schema, or feature change:

  ```sql
  UPDATE acore_auth.realmlist
  SET flag = 0
  WHERE id = 1;
  ```

  This corrected `acore_auth.realmlist.id = 1` from `flag = 3` to `0`. The
  verified realm is `AzerothCore DEV` at `127.0.0.1:8085`, build `12340`.
- 2026-09-20: The user then ran the tracked `./stop.sh`, `./status.sh`, and
  `./start.sh` lifecycle sequence, waited 45 seconds, and ran `./status.sh`
  again. The user additionally observed listeners on `0.0.0.0:3724` and
  `0.0.0.0:8085`, plus authserver realm-load evidence. The stack was left
  running.

### Lifecycle result

- **PASS — clean stop and restart:** user-observed tracked lifecycle output
  confirmed authserver and worldserver stopped with SIGTERM, then both were
  confirmed stopped before startup.
- **PASS — healthy managed processes:** after restart and a 45-second wait,
  `status.sh` reported authserver PID `30512` and worldserver PID `30522`
  running at that final check.
- **PASS — network and log readiness evidence:** authserver listened on
  `0.0.0.0:3724`; worldserver listened on `0.0.0.0:8085`; authserver log
  evidence confirmed realm `AzerothCore DEV` loaded. This combines lifecycle,
  listener, and current-startup log evidence rather than treating process
  existence alone as health proof.
- **FAIL — historical initial automated startup attempt:** the initial agent
  `start.sh` invocation failed before worldserver startup. The discovered cause
  was the pre-existing `realmlist.flag = 3` DEV realm configuration, not a
  harness-introduced database change. This historical failure does not change
  the final **PASS** lifecycle capability result after the DEV-state correction.
- **Meaningful consistency finding:** the installed runtime was inconsistent
  with its intended local realm availability while the realm flag was `3`.
  After the verified correction to `0`, the clean lifecycle validation found no
  further runtime inconsistency.

### Deferred harness improvement

Do not implement during this audit. Runtime validation must fail fast: after a
`start.sh` failure, immediately check status, inspect only recent/relevant log
output, check relevant processes and listening ports, run a small number of
targeted diagnostics, then return **FAIL** or **BLOCKED** rather than pursuing
open-ended investigation.

### Completion review

- 2026-09-20: Independent `ac-review` reviewed this plan for record accuracy,
  internal consistency, and lifecycle result distinction. It identified the
  incomplete first disposable-table record, missing runtime-artifact detail,
  lifecycle/database scope ambiguity, stale intermediate completion wording,
  and insufficient provenance. The plan now documents the unavailable first
  table details, runtime-artifact limitation, user-observed lifecycle commands,
  agent-versus-user database scope, and phase-specific completion. No runtime,
  database, or source action was taken to address documentation findings.
- No component documentation, ADR, debt-register, or identifier update is
  warranted: this is a completed, local, task-specific audit record. The
  deferred harness improvement is retained above for future implementation.

## Next action

Archived as a completed smoke-test plan. Do not repeat runtime or database
validation without a new task.
