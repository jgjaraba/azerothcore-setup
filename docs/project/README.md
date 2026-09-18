# AzerothCore Project Knowledge

This directory is the durable source of truth for the custom AzerothCore
project.

Its contents must remain independent of OpenCode sessions, individual AI
models, and any specific coding-agent product.

## Startup protocol

Before substantial project work:

1. Regenerate `generated/ENVIRONMENT.md`.
2. Read `ARCHITECTURE.md`.
3. Check `../../../plans/active/` for the relevant active execution plan.
4. Read only the component documentation relevant to the task.
5. Consult ADRs when a previous architectural decision is relevant.
6. Inspect the real Git state before making assumptions about code versions or
   pending changes.

## Structure

- `ARCHITECTURE.md`
  Stable high-level architecture and project-wide engineering principles.

- `components/`
  Durable knowledge about individual subsystems.

- `decisions/`
  Architectural Decision Records (ADRs).

- `debt/`
  Known technical debt and intentionally deferred work.

- `generated/`
  Facts reconstructed automatically from the current environment.

Execution plans live separately under:

`~/azerothcore-setup/plans/`

Existing operational and feature-specific documentation may continue to live in
`~/azerothcore-setup/docs/`.

## Source-of-truth policy

Prefer information in this order:

1. Current repositories and runtime environment for directly measurable facts.
2. Durable project documentation and accepted ADRs.
3. The current active execution plan.
4. The current task requirements.
5. Conversation history only as non-authoritative context.

If two sources disagree, investigate the discrepancy.

## Documentation policy

Store:

- verified behaviour;
- durable architectural knowledge;
- project constraints;
- important design decisions;
- known limitations;
- reproducible procedures.

Do not store:

- conversation transcripts;
- chain-of-thought;
- temporary speculation;
- facts that can be reconstructed reliably by tooling.

Generated environment facts must be regenerated rather than manually
maintained.

When durable information changes, update its authoritative document instead of
adding contradictory notes elsewhere.
