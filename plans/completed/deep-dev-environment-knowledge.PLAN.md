# Task: Deep DEV environment knowledge model

Status: completed
Created: 2026-09-20
Last updated: 2026-09-20

## Goal

Extend the durable project knowledge base with evidence-backed documentation of
how the local AzerothCore DEV environment is constructed, customized, and
operated, including its observed databases and runtime deployment boundary.

## Scope

### Included

- Read-only investigation of the core checkout, every independent module,
  project control repository, DEV databases, and installed runtime.
- Evidence-backed documentation, identifier inventory, reproducibility analysis,
  and risk/open-question register under `docs/project/`.
- Regenerated environment inventory and this durable execution plan.

### Excluded

- Any core, module, SQL implementation, database, runtime-config, build,
  install, client, process, Git history, or publication change.

## Baseline

- The environment inventory was regenerated before research. It records the
  current repository revisions, branches, remotes, and clean initial trees.
- The core checkout is on protected `master` and remains read-only. The setup
  repository is on `docs/deep-project-knowledge`, an appropriate documentation
  feature branch.
- Completed bootstrap, deep-component, and custom-SQL-ordering audits provide
  source-level documentation; they did not inspect DEV database contents or
  runtime configuration values.

## Constraints

- Use only local DEV resources; never discover or access production systems.
- Read databases only through the configured local login path; do not expose
  credentials or connection strings.
- Keep current revisions, branches, and worktree state in generated inventory.
- Do not stage, commit, push, switch branches, build, migrate, or change
  processes.

## Research findings

- Existing durable documentation and completed audits were inspected before new
  investigation. They establish the current component structure and identify
  database/runtime evidence as the principal remaining knowledge gap.
- Parallel read-only research has completed for core/runtime, all module
  repositories, setup-owned assets, and the four local DEV databases. Its
  reported evidence requires targeted primary-source/query verification before
  documentation is treated as authoritative.
- Targeted primary source/configuration inspection and read-only DEV queries
  verified static module integration, core lineage signals, direct ecosystem
  APIs, build/runtime layout, database topology/update-state gap, project custom
  SQL rows, MorphSummon feature state, and identifier presence. Documentation
  now records these observations with dates and separates them from deployment
  or behavior claims.

## Decisions

- Extend the existing component-oriented knowledge base rather than create one
  monolithic report. Add focused documentation only where current documents do
  not have an authoritative home for observed deployment state, identifiers,
  reproducibility, and risks.

## Implementation

- Created this durable plan.
- Expanded architecture, runtime, database, module, client, and knowledge-index
  documentation; added a custom-identifier registry and a durable debt register.

## Validation

- Ran `scripts/agent/refresh-environment.sh` successfully before research.
- Inspected project index, existing architecture/components, completed audits,
  generated inventory, and current Git status/remotes for core and setup.
- Ran read-only MySQL metadata/aggregate queries through the configured DEV login
  path, DBC dry-run record checks, documentation whitespace/line-length/secret
  searches, and `git diff --check`.
- Regenerated `generated/ENVIRONMENT.md` after documentation milestones.
- Independent review found an installed-server/tracked-DBC mismatch, confirmed
  effective Transmog token settings, and corrected Playerbots version-table,
  identifier-set, stale-open-question, and plan-consistency documentation.
- Final review found stale Forsaken Paladin creation/outfit attribution. Current
  manifest SQL contains no `CharStartOutfit` `9000`/`9001` contract, so those
  unsupported registry/client claims were removed.
- Re-ran environment generation, `git diff --check`, documentation line-length
  and secret-exposure searches, and Git-status inspection for core, setup, and
  every independent module. All checks passed; only task-owned setup
  documentation/plan paths are changed and every implementation tree is clean.
- Inspected the final relevant documentation and plan diff. Independent
  `ac-review` review was completed in three passes; all actionable findings were
  verified against primary evidence and corrected. No new long-lived
  architectural decision was made, so no ADR was required; existing ADRs remain
  the control-plane and custom-SQL-manifest decisions.

## Open issues

- No tested core/module compatibility matrix, clean-build provenance, complete
  cross-database deployment/recovery workflow, or companion-addon/client-MPQ
  parity baseline is tracked.
- The installed server Item.dbc is observably out of alignment with tracked
  custom item IDs; its cause and player-visible effect require a separate
  deployment/client validation task.

## Next exact action

No further task action. Future work should address the documented deployment
discrepancy, reproducibility gaps, and compatibility/behavior validation before
changing affected components.
