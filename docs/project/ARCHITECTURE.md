# AzerothCore Project Architecture

## Status

Bootstrap audit completed on 2026-09-18. A source-level module and custom-world
SQL component audit completed on 2026-09-19. Mechanically detectable repository
revisions and working-tree state remain in `generated/ENVIRONMENT.md`.

## Purpose

This document describes the stable architecture of the custom AzerothCore
environment.

Detailed subsystem knowledge belongs in `components/`.

Runtime and repository facts that can be detected automatically belong in
`generated/ENVIRONMENT.md`.

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
- operational scripts;
- durable project documentation;
- execution plans;
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

## Verified integration model

- The local core checkout, project control repository, and independently
  versioned modules retain separate repository histories. Current branches and
  revisions are generated environment state.
- The observed CMake configuration uses static modules and installs into
  `~/azerothcore/env/dist`. Runtime configuration and module configuration
  files in that install tree are intentionally ignored by the core repository.
- Project-owned SQL is kept separately under
  `~/azerothcore-setup/data/sql/custom/`; the current installer applies only
  the `db_world` subtree to the local world database.
- Client customizations are distributed from the control repository as DBC
  resources and separate regular and HD client MPQ patches.

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

The current agent-enabled environment is intended for development and
validation.

Production systems must not be modified implicitly by an automated agent.

## Verification principle

A claim that something builds, passes tests, works in-game, or has been
validated must correspond to validation that was actually performed.

## Audit boundary

The bootstrap audit established the current development topology and explicitly
identified the absence of tracked update and recovery automation. The later
component audit inspected module source/data and project custom world SQL, but
did not connect to databases, inspect credentials, run the servers, or validate
in-game behavior.
