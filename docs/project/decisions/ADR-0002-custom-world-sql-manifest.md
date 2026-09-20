# ADR-0002: Custom world SQL manifest

Status: Accepted
Date: 2026-09-20

## Context

The project-owned world SQL installer previously derived execution order from
lexically sorted filenames. That order did not represent dependencies between
the Dark Rider curio item definitions, vendor templates, vendor inventory, and
loot. Filename order is also vulnerable to future accidental omissions.

## Decision

`data/sql/custom/db_world/manifest.txt` is the authoritative, exact ordered
inventory for project custom world SQL. The installer validates the manifest
before database access and fails if an entry is missing, duplicated, malformed,
or if a SQL file is omitted. Custom SQL remains a post-module overlay: external
module data prerequisites must be installed before this manifest is applied.

The installer continues to execute one SQL file at a time and stop on the first
MySQL error. The manifest does not add an installation ledger or make the batch
atomic.

## Alternatives considered

### Numeric filename prefixes

They conflate SQL identity with order, create unnecessary rename churn, and do
not ensure every file is deliberately registered.

### An ordered list embedded in the installer

It would couple the SQL inventory to operational shell logic rather than keep a
small, reviewable data manifest beside the SQL files.

### Database migration ledger

A once-only migration system would change existing rerun behavior and introduce
database state and recovery concerns beyond the ordering problem.

## Consequences

### Positive

- Installation order is explicit, deterministic, and version controlled.
- Validation fails before database access when the SQL inventory drifts.
- Existing SQL filenames and rerun behavior are preserved.

### Negative / trade-offs

- Adding or removing SQL requires a corresponding manifest update.
- The batch remains non-atomic; successfully applied earlier files can persist
  if a later SQL file fails.

## References

- `data/sql/custom/db_world/manifest.txt`
- `scripts/apply-db-world.sh`
- `components/custom-world-sql.md`
