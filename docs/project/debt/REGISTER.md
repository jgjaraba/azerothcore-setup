# Technical debt register

This register tracks durable, evidence-backed risks. It does not assert a
priority order and does not track task-specific open issues.

## DEBT-001: No ecosystem compatibility baseline

- **Type:** Architectural risk.
- **Evidence:** Playerbots requires a compatible fork; Individual Progression,
  Dungeon Clear, MultiBot Bridge, and Character Services have direct or
  documented compatibility dependencies. No immutable tested matrix is tracked.
- **Consequence:** A core or module update can compile or deploy incompletely,
  or regress runtime behavior without a known rollback target.
- **Action trigger:** Before updating any member of this ecosystem.

## DEBT-002: Cross-database deployment and recovery are incomplete

- **Type:** Operational risk.
- **Evidence:** Four DEV databases are present. Project SQL installer applies
  only a non-atomic world overlay; no tracked full module-SQL, backup, restore,
  or rollback workflow exists.
- **Consequence:** A partial update can leave persistent state difficult to
  reconstruct or recover.
- **Action trigger:** Before database reset, module update, or non-disposable
  data change.

## DEBT-003: Effective runtime configuration is untracked

- **Type:** Reproducibility risk.
- **Evidence:** `env/dist` is ignored; effective module settings and database
  credentials are local deployment state.
- **Consequence:** Git assets cannot fully recreate behavior or safely explain
  configuration drift.
- **Action trigger:** Before recreating DEV or changing an effective setting.

## DEBT-004: Client artifact provenance and addon pinning are incomplete

- **Type:** Client/server compatibility risk.
- **Evidence:** DBC and regular/HD MPQs are tracked, but their construction,
  parity, deployed copies, and companion addon revisions are not documented.
- **Consequence:** Server data can be deployed without matching visible/client
  behavior.
- **Action trigger:** Before changing DBC, display, ExtendedCost, addon protocol,
  or client patch data.

## DEBT-005: Custom identifiers lack a decided allocation policy

- **Type:** Update/collision risk.
- **Evidence:** `CUSTOM-IDENTIFIERS.md` records project references and limited
  DEV checks, but no approved global allocation, retirement, or collision
  procedure exists.
- **Consequence:** Future module/core/client additions can collide or overwrite
  data, especially where SQL deletes/recreates reserved entries.
- **Action trigger:** Before allocating or reusing an ID/range.

## DEBT-006: MorphSummon unlock feature lacks behavioral validation

- **Type:** Open validation risk.
- **Evidence:** Current fork source and DEV schema/data are present; no build or
  live unlock/persistence test is recorded.
- **Consequence:** Update or deployment can retain orphaned data or silently
  break acquisition/filtering behavior.
- **Action trigger:** Before promoting, rebasing, or updating the feature.

## DEBT-007: Installed server Item.dbc diverges from tracked custom items

- **Type:** Verified deployment discrepancy.
- **Evidence:** On 2026-09-20, tracked `dbc/Item.dbc` contained `90001`–`90005`,
  while installed server `bin/dbc/Item.dbc` contained neither those nor
  `91001`–`91079`; SHA-256 hashes differ. Matching world item templates exist.
- **Consequence:** Database item rows can lack matching installed server DBC
  records, making server/client data behavior unsafe to assume.
- **Action trigger:** Before any custom item, DBC, MPQ, or MorphSummon change.

## DEBT-008: Custom world SQL manifest was incomplete — resolved

- **Type:** Resolved operational blocker; manifest drift remains a regression
  risk.
- **Evidence:** Eight omissions previously caused `--validate` to fail before
  database access. `scripts/apply-db-world.sh --validate` now passes, verifying
  coverage and existence of all 19 SQL files exactly once. Review of the SQL
  dependencies established the dungeon vendor currency → NPC → inventory → loot
  order; the other newly registered files have no ordering dependency on one
  another at the custom-SQL object level. The omissions arose when feature SQL
  was added without updating the manifest, contrary to ADR-0002.
- **Consequence:** No current blocker after successful manifest validation.
  Future unregistered SQL still makes the installer fail closed.
- **Repair:** Completed; keep the manifest in the same change as every custom
  world SQL addition/removal and run `scripts/apply-db-world.sh --validate`.
- **Action trigger:** Whenever custom world SQL is added or removed.
