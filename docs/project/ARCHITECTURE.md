# AzerothCore Project Architecture

## Status

Bootstrap audit completed on 2026-09-18. A source-level module and custom-world
SQL component audit completed on 2026-09-19. A DEV environment knowledge pass
completed on 2026-09-20.

Mechanically detectable facts — branches, revisions, working-tree state,
running processes — are not recorded here. Inspect the live repositories and
the live machine instead.

## Purpose

This document describes the stable architecture of the custom AzerothCore
environment.

Detailed subsystem knowledge belongs in `components/`. Feature design contracts
belong in `features/`. Reusable gotchas belong in `LEARNINGS.md`.

## Repository roles

### AzerothCore working tree

`~/azerothcore`

Upstream-oriented development working tree.

The checkout itself must not be treated as the durable store for private
project knowledge.

### Project control repository

`~/azerothcore-setup`

Canonical home for project-owned assets such as:

- custom SQL;
- client assets and patches;
- DBC resources;
- core source patches;
- operational scripts;
- durable project documentation;
- coding-agent harness configuration.

## Component map

- `components/runtime.md` — local build/install layout, configuration ownership,
  and managed server lifecycle scripts.
- `components/data-and-database.md` — database configuration boundary and
  project-owned custom world SQL installation.
- `components/modules.md` — independently versioned modules and their build
  integration, standalone module behavior, and relationship index.
- `components/playerbots-ecosystem.md` — the coordinated Playerbots,
  Individual Progression, Character Services, Dungeon Clear, and MultiBot
  Bridge compatibility boundary.
- `components/custom-world-sql.md` — verified project world-SQL behavior,
  dependency chains, assumptions, and update/validation concerns.
- `components/client-assets.md` — DBC resources, client patch distribution, and
  addon inventory.
- `features/` — durable design contracts for custom content, such as the
  Forsaken Paladin quest chains.
- `LEARNINGS.md` — verified operational and engineering gotchas.
- `CUSTOM-IDENTIFIERS.md` — evidence-backed project identifier inventory and
  its collision-check boundary.
- `decisions/` — architectural decision records.
- `debt/REGISTER.md` — durable architectural, operational, and update risks.

## Verified integration model

- The local core checkout, project control repository, and independently
  versioned modules retain separate repository histories. Current branches and
  revisions are read from the live repositories.
- The observed CMake configuration uses static modules and installs into
  `~/azerothcore/env/dist`. Runtime configuration and module configuration
  files in that install tree are intentionally ignored by the core repository.
- Project-owned SQL is kept separately under
  `~/azerothcore-setup/data/sql/custom/`; the current installer applies only
  the `db_world` subtree to the local world database.
- Client customizations are distributed from the control repository as DBC
  resources and separate regular and HD client MPQ patches.

## End-to-end dependency chain

The local DEV stack is assembled through the following dependency chain:

```text
core lineage -> module revisions -> CMake configuration -> static worldserver
integration -> installed binaries and effective configuration -> core/module
database data -> project world-SQL overlays -> server DBC -> client MPQs/addons
-> live validation
```

**VERIFIED.** The observed build cache selects static modules; core CMake
collects their source into a single static `modules` library and generates its
loader. Playerbots additionally enables `MOD_PLAYERBOTS` compilation paths.
Consequently, a core or static-module source change is not a runtime-plugin
replacement: it requires a compatible rebuild/install and server restart.

**UNKNOWN.** No build or live validation proves that the currently observed
core, module, database, client, and addon revisions are mutually compatible.

## Core lineage boundary

**VERIFIED.** The core origin is a Grimfeather AzerothCore fork. Its current
history contains recurrent upstream/AzerothCore and Playerbots merge history,
and its source/build metadata contains Playerbots-specific compilation support.
The Playerbots ecosystem therefore depends on more than an ordinary separately
loaded module. Exact divergence from official AzerothCore and a supported
revision matrix remain UNKNOWN; inspect the live repositories and relevant Git
history before updating this boundary.

## Reproducibility boundary

- **Source:** repository revisions are inventoried, but no compatibility lock
  manifest exists.
- **Build:** the current cache exposes toolchain/options; a clean-build recipe is
  not tracked.
- **Database:** the custom-world manifest exists; full cross-database deployment
  and recovery do not.
- **Runtime:** effective non-secret settings and secret provisioning are ignored
  deployment state.
- **Client:** DBC/MPQ/addon assets are tracked, but complete provenance and
  parity are not established.
- **Operations:** lifecycle and world-SQL scripts exist; complete update,
  backup, rollback, and validation workflow does not.

This table records architecture, not proof that any missing input is unavailable
elsewhere. See the component documents and debt register for evidence and open
questions.

## Operational boundaries

- The tracked lifecycle scripts manage only the local development authserver
  and worldserver installation. They use explicit binary and configuration
  paths to avoid acting on unrelated processes.
- No tracked project script or documentation establishes an automated upstream
  update workflow, database backup, restore, or recovery procedure. These
  remain operational gaps rather than implied capabilities.

## Customization strategy

When multiple technically correct implementations are possible, prefer:

1. Database-only customization when sufficient and maintainable.
2. AzerothCore module when database-only implementation is insufficient.
3. Core modification only when the previous approaches are inappropriate.

This ordering is a maintainability preference, not an absolute rule.
Correctness and compatibility take precedence.

## Update safety

Persistent customizations should be:

- reproducible;
- reviewable;
- version controlled;
- as isolated from upstream code as practical;
- resilient to upstream AzerothCore and module updates.

## Environment boundaries

The current agent-enabled environment is a disposable development VM intended
for development and validation.

Nothing on this machine is production. Production systems must not be modified
implicitly by an automated agent, and the DEV VM is not expected to preserve its
previous state between tasks.

## Verification principle

A claim that something builds, passes tests, works in-game, or has been
validated must correspond to validation that was actually performed.

## Audit boundary

The bootstrap audit established the current development topology and explicitly
identified the absence of tracked update and recovery automation. A later
component audit inspected module source/data and project custom world SQL. A
later environment pass inspected the four DEV databases and the installed
runtime. None of them demonstrated full in-game behavior, and no later
inspection should be read as evidence that they did.
