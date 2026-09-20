# Task: Custom world SQL ordering

Status: completed
Created: 2026-09-20
Last updated: 2026-09-20

## Goal

Make custom `db_world` SQL installation deterministic and dependency-correct on
a fresh environment through a version-controlled explicit ordering mechanism.

## Scope

### Included

- `apply-db-world.sh`, every current custom `db_world` SQL file, and relevant
  setup-repository documentation.
- Manifest validation for missing, omitted, and duplicate SQL entries.
- Static/shell validation and independent review.

### Excluded

- Database execution or modification, SQL content changes, renaming existing
  SQL solely to influence ordering, and changes outside `azerothcore-setup`.

## Baseline

- Environment regenerated on 2026-09-20; `azerothcore-setup` is on
  `fix/custom-sql-ordering` at the revision recorded in generated environment
  state and its working tree was clean before task work.
- AzerothCore is clean on protected `master` and will remain read-only.
- Before this task, `apply-db-world.sh` discovered and lexically sorted SQL
  files. The generated inventory lists ten current
  `data/sql/custom/db_world/*.sql` files.

## Constraints

- Preserve stop-on-first-error behavior and do not connect to or modify MySQL.
- Account for each current SQL file; detect manifest missing, omitted, and
  duplicate entries where practical.
- Do not stage, commit, push, create a PR, or alter branches/history.

## Research findings

- The completed deep component audit documents dependency chains, but its
  historical Forsaken Paladin filenames do not match the current ten-file
  inventory. Inspection confirmed that only `race_class_5_2.sql` remains, so no
  current Paladin-polish order can be encoded.
- Inspection of all ten current SQL files confirmed the only internal ordering
  chain is `raid_gear_vendor.sql`, `raid_gear_vendor_npc.sql`,
  `raid_gear_vendor_item.sql`, then `raid_gear_vendor_loot.sql`. The mount
  overlay and raid Naxx40 loot have external Individual Progression data
  prerequisites.

## Decisions

- Use a plain, line-oriented `data/sql/custom/db_world/manifest.txt` as the
  version-controlled exact inventory and order. It needs no parser, keeps order
  separate from SQL identity, avoids rename churn, and is easy to review.
- Fail closed before MySQL access when the manifest is missing, malformed,
  empty, contains duplicates or missing files, or omits a discovered SQL file.
  Keep the existing per-file MySQL invocation and stop-on-first-error behavior.

## Implementation

- Created this durable execution plan before implementation.
- Added the explicit SQL manifest; updated the installer to validate it and
  support a database-free `--validate` mode; updated the relevant component
  documentation and ADR.
- Updated discovery to fail closed if the `find` command fails, following
  independent review.
- Reopened for a final correctness pass. `SQL_DIR` and `MANIFEST` now accept
  environment overrides so `--validate` can exercise isolated temporary
  fixtures without modifying the real SQL inventory or accessing MySQL.

## Validation

- Ran `scripts/agent/refresh-environment.sh` successfully.
- Inspected project knowledge index, architecture, database/custom-SQL
  component documentation, deep-audit plan, relevant SQL guidelines, active
  plans, installer script, generated inventory, and Git status/branch in both
  repositories.
- Ran `bash -n scripts/apply-db-world.sh`,
  `scripts/apply-db-world.sh --validate`, and `git diff --check`; all passed.
- `shellcheck` is not installed in the environment.
- Independent review found discarded SQL-discovery errors and stale module/plan
  documentation. The discovery failure is now handled before MySQL access and
  the documentation is corrected.
- Re-ran `bash -n scripts/apply-db-world.sh`,
  `scripts/apply-db-world.sh --validate`, and `git diff --check`; all passed.
- Follow-up independent review found no remaining actionable issues.
- Final correctness pass is in progress; the plan remains active until its
  database-free negative validation and final review are recorded.
- Added an environment-overridable SQL root and manifest path solely to permit
  isolated `--validate` fixtures; default installer paths are unchanged.
- Ran database-free temporary-fixture tests. All invalid cases emitted a
  specific error, printed the pre-database abort message, and exited `1`:
  missing manifest, empty manifest, invalid manifest entry, duplicate entry,
  missing listed SQL file, omitted SQL file, and simulated `find` failure.
- Final positive checks passed: `bash -n scripts/apply-db-world.sh`,
  `scripts/apply-db-world.sh --validate`, and `git diff --check`.
- Final documentation search found no stale current-behavior claim of lexical
  ordering. The ADR's lexical-order reference is explicitly historical.
- Final independent review of the complete tracked and untracked change found
  no actionable findings.
- Completion check re-inspected the final relevant diff, durable component
  documentation, ADR, limitations, and repository status. No database access,
  staging, commit, push, or PR was performed.

## Open issues

- No implementation issues. The SQL batch remains non-atomic and its external
  module prerequisites require operational sequencing outside this installer.

## Next exact action

No further task action. Before any database use, install external module
prerequisites and run `scripts/apply-db-world.sh --validate`.
