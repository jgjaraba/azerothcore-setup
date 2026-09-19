# Task: Bootstrap audit of the current AzerothCore project and development environment

Status: completed
Created: 2026-09-18
Last updated: 2026-09-18

## Goal

Establish a verified, durable baseline for the current AzerothCore project and
development environment without modifying application or customization state.

## Scope

### Included

- Regenerate and inspect the generated environment state.
- Inspect the actual Git state of the primary repositories identified by that state.
- Create a durable audit plan and identify the next source-based audit action.

### Excluded

- Changes to AzerothCore, modules, SQL customizations, configuration, or runtime services.
- Builds, tests, database operations, and production changes.

## Baseline

- `scripts/agent/refresh-environment.sh` regenerated
  `docs/project/generated/ENVIRONMENT.md` on 2026-09-18.
- The generated state identifies `/home/dev/azerothcore` as `master` at
  `529b659668bcd8b1cfbf9acc44f40eb6ff830fe1`; its working tree is clean.
- Direct Git inspection confirmed the AzerothCore working tree is clean.
- Direct Git inspection confirmed pre-existing pending changes in
  `/home/dev/azerothcore-setup` (two modified and two untracked custom SQL
  files) and in `modules/mod-morphsummon` (one modified source file and four
  untracked paths). These are outside this audit's scope and must be preserved.
- Project architecture documentation reports that the bootstrap audit remains
  pending; no component documentation exists yet beyond its index.

## Constraints

- Do not modify unrelated pending work in either repository.
- Treat generated environment facts as mechanically regenerated state.
- Do not configure, build, run tests, access databases, or modify production
  systems unless later explicitly required.
- Record only source-verified findings in durable documentation.

## Research findings

- The project control repository owns private assets, documentation, execution
  plans, and harness configuration; the AzerothCore checkout is the
  upstream-oriented development tree.
- The documented customization preference is database-only, then module, then
  core changes when correctness and compatibility allow.
- The observed CMake cache installs into `~/azerothcore/env/dist`, has static
  modules enabled, and has testing disabled. The install contains authserver,
  worldserver, and module configuration pairs for the independently checked-out
  modules.
- Login, character, and world database connection settings are present in the
  ignored local runtime configurations. Project-owned SQL currently contains
  only `db_world` files. `scripts/apply-db-world.sh` applies all such files in
  lexicographic order to `acore_world` through the `azeroth-dev` login path and
  stops on the first failure.
- The local lifecycle scripts are scoped to the development installation and
  identify managed processes by both executable and configuration paths.
- Client assets are project-owned DBC resources plus separate regular and HD
  `patch-Z.mpq` files; the repository also distributes two addon archives.
- No tracked project update, database backup, restore, or recovery automation
  was found.

## Decisions

- Kept this plan active while the bootstrap audit was in progress because the
  work was non-trivial and had to be resumable across sessions.
- Do not read subsystem-specific component documentation: none exists, and the
  component index directs that documents be created only from verified audit
  findings.
- Record the absence of tracked update and recovery automation as an audit
  finding rather than infer an undocumented operational process.

## Implementation

- Added this durable execution plan.
- Updated `docs/project/ARCHITECTURE.md` with the verified integration model,
  operational boundaries, and component map.
- Added component documentation for runtime/configuration, database/custom
  data, modules, and client assets.

## Validation

- Ran `/home/dev/azerothcore-setup/scripts/agent/refresh-environment.sh`.
  Result: regenerated `docs/project/generated/ENVIRONMENT.md` successfully.
- Ran `git status --short`, `git diff --stat`, and `git diff --cached --stat`
  in `/home/dev/azerothcore`, `/home/dev/azerothcore-setup`, and
  `modules/mod-morphsummon`.
  Result: confirmed the clean core tree and the pre-existing pending changes
  recorded above.
- Re-ran `/home/dev/azerothcore-setup/scripts/agent/refresh-environment.sh`
  on 2026-09-18 and inspected the active plan, project documentation, and
  current Git state before continuing.
- Inspected the control repository's tracked runtime scripts, custom SQL
  inventory, client asset layout, module CMake cache, and ignored install
  configuration paths. No database connections, server processes, builds, or
  tests were run.
- Re-ran `/home/dev/azerothcore-setup/scripts/agent/refresh-environment.sh`
  after completing documentation. Result: generated state reflects the final
  audit working-tree path count.
- Received independent documentation review. Result: corrected the component
  path to generated state, qualified the backup-automation finding, and moved
  this completed plan from `plans/active/` to `plans/completed/`.

## Open issues

- A documented and tested upstream update procedure is still needed.
- A documented and tested database backup, restore, and recovery procedure is
  still needed.

## Next exact action

Before changing core, module, SQL, or operational state, start a dedicated task
from this documented baseline and verify its affected component's current
repository and runtime state.
