# ADR-0003: Core source patches in azerothcore-setup

Status: Accepted
Date: 2026-09-21

## Context

Some customizations cannot be expressed with database data, modules, or
configuration alone because they require changes to compiled AzerothCore
source code. Up until now, azerothcore-setup has tracked only custom SQL
(ADR-0002) and client MPQ patches. There is no reproducible mechanism for
capturing, validating, and reapplying core source divergences after an
upstream update or a fresh DEV server installation.

## Decision

Core source divergences are represented as tracked `git diff` patches under
`patches/core/` and applied by `scripts/apply-core-patches.sh`.

The mechanism:

- `patches/core/manifest.txt` is the ordered, exact inventory of patches.
- Each patch is a plain `git diff` against a pinned base commit.
- `scripts/apply-core-patches.sh --validate` reports, for every patch, whether
  it is already applied, applies cleanly, or conflicts with the current tree.
- `scripts/apply-core-patches.sh` applies only patches that are not already
  present and that pass a dry-run check; it fails fast on conflict.
- Each patch directory contains a README documenting what it changes, the
  pinned base commit, apply/remove/validate/rollback procedures, and
  upstream-update sensitivity.

Patches are applied directly to the AzerothCore working tree. Because
AzerothCore modules are statically linked into the worldserver binary, a
rebuild and reinstall is required after applying any core patch.

## Alternatives considered

### Edit source directly and leave changes uncommitted in the working tree

Rejected: changes would be lost on the next clean checkout or upstream update
and would not be reproducible on another DEV server.

### Maintain a long-lived fork branch of AzerothCore

Rejected: it increases merge burden and couples the customization to a
particular Git history strategy. The project already consumes AzerothCore as a
primary repository and uses azerothcore-setup for durable project assets. A
patch mechanism keeps the divergence small, reviewable, and explicit.

### Use `git format-patch` commits

Rejected: the agent workflow does not create commits in implementation
repositories, and the user owns branch/history operations. A `git diff` patch
can be generated from the working tree without commits.

## Consequences

### Positive

- Core source customizations are version controlled and reproducible.
- Validate-before-apply prevents silent partial application and surfaces
  upstream conflicts early.
- The manifest pattern mirrors the existing ADR-0002 SQL manifest, keeping
  operational conventions consistent.

### Negative / trade-offs

- Patches are not atomic across multiple files; if one hunk fails, the
  installer stops and the tree may be partially patched.
- `git diff` patches do not carry three-way merge metadata, so conflicts must
  be resolved manually rather than via `git apply --3way`.
- Every patch requires a rebuild of the core and a server restart.
- The base commit must be updated when the patch is regenerated after an
  upstream change.

## References

- `patches/core/`
- `scripts/apply-core-patches.sh`
- ADR-0004: Player-owned combo points
