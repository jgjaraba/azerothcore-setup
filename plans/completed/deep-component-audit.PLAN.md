# Task: Deep component audit

Status: completed
Created: 2026-09-19
Last updated: 2026-09-19

## Goal

Expand the durable project component model from verified inspection of every
independent module repository and every project-owned custom world SQL file.

## Scope

### Included

- Module source, documentation, configuration templates, database data, and
  Git working-tree inspection for all repositories under `~/azerothcore/modules/`.
- Source-based analysis of all SQL files under
  `~/azerothcore-setup/data/sql/custom/`.
- Durable documentation and audit-plan updates only.

### Excluded

- Changes to module/core source, SQL, databases, runtime configuration,
  builds, installs, Git staging, commits, or cleanup of pre-existing work.

## Baseline

- Environment state was regenerated on 2026-09-19; generated repository
  revisions and inventory are in `docs/project/generated/ENVIRONMENT.md`.
- The generated snapshot records the current repository worktree state. Setup
  already contains bootstrap-audit documentation and custom SQL work;
  MorphSummon already contains source, SQL, and IDE work. Those pre-existing
  states must be preserved.
- The bootstrap documentation provides high-level module and custom-SQL
  boundaries but not source-level component behaviour.

## Constraints

- Keep transient repository branch, commit, and dirty-state facts in generated
  environment state, not semantic component documents.
- Distinguish verified behaviour, project-specific customization, unresolved
  questions, and recommendations in the component documentation.
- Do not infer SQL or module behaviour solely from names.

## Research findings

- Read-only source research completed for all ten module repositories and all
  twelve project custom world SQL files. The major verified cluster is
  Playerbots: Dungeon Clear and MultiBot Bridge directly depend on it;
  Individual Progression has a qualified compatible-core/bot-aware relationship;
  Character Services directly depends on Individual Progression. The AH bot
  explicitly must not use Playerbot characters.
- Project custom SQL has explicit dependency chains for the Forsaken Paladin
  implementation, raid-gear vendors/currencies, and Individual Progression
  riding/mount overrides.
- Architecture review selected a module catalog plus a focused Playerbots
  ecosystem document and a single manifest grouped by custom-SQL feature chain.
  It identified that lexical custom-SQL application does not honor current
  dependencies, so documentation must not represent the batch as reproducible.

## Decisions

- Use focused component documents for complex modules and grouped documents
  only where verified relationships justify grouping.

## Implementation

- Created this durable execution plan.
- Added `components/playerbots-ecosystem.md` and
  `components/custom-world-sql.md`; expanded the module catalog and relevant
  client/architecture indexes from verified research.
- Corrected the Paladin trainer manifest: `race_class_5_2.sql` removes existing
  spawns/addons but leaves their final creation to
  `forsaken_paladin_phase1_1.sql`.

## Validation

- Ran `scripts/agent/refresh-environment.sh` successfully.
- Inspected Git status and diff statistics for the core, setup repository, and
  every module repository before making changes.
- Completed read-only research-agent audits of all installed modules and custom
  SQL. No implementation repositories were modified by that research.
- Completed architecture review of component boundaries and update safety.
- Completed independent documentation review and applied its findings, including
  qualified Playerbots relationships, MultiBot Bridge persistence, SQL ordering
  and portability, and client-data contracts.
- Ran documentation whitespace and line-length checks plus `git diff --check`.
- Re-inspected core, setup, and module Git status. No audit change was made to
  core/module source, SQL, databases, or runtime configuration; setup SQL and
  MorphSummon dirty state remain pre-existing work.
- Independent review found and the documentation now corrects the trainer-spawn
  ownership error. Its provenance concern was not adopted: component documents
  deliberately defer mutable repository revisions to the regenerated environment
  inventory, as required by this plan.
- Re-ran documentation whitespace and 120-column checks after the correction;
  both passed. Re-inspected the complete relevant documentation and plan diffs.
- Re-review found no remaining actionable correctness or scope findings and
  confirmed that this documentation-only audit needs no ADR.

## Open issues

- The documented custom-SQL ordering defect, custom-ID/DBC registry, curio
  `BagFamily` contradiction, Transmog token target/configuration, and complete
  reproducible deployment inputs require future design and live/database work.

## Next exact action

No further audit action. Resolve the documented ordering, ID/DBC, and deployment
questions in separate implementation tasks before applying related changes.
