# AzerothCore Project Architecture

## Status

Bootstrap audit pending.

This document intentionally contains only stable project-wide principles until
the current environment has been audited from source.

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

## Pending bootstrap

The initial audit must populate at least:

- core repository and branch strategy;
- independent module inventory;
- build/install layout;
- database topology;
- custom SQL architecture;
- configuration ownership;
- client-side customization strategy;
- update workflow;
- backup/recovery boundaries;
- component documentation map.
