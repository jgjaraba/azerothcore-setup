# ADR-0001: Keep durable project knowledge outside the AzerothCore upstream checkout

Status: Accepted
Date: 2026-09-18

## Context

The AzerothCore working tree follows an upstream repository and already ships
its own AGENTS.md and `.agents/` infrastructure.

Private project knowledge previously depended too heavily on OpenCode session
state and local OpenCode configuration.

That makes continuity vulnerable to:

- session replacement;
- model changes;
- context compaction;
- OpenCode upgrades;
- recreating the AzerothCore working tree.

## Decision

`~/azerothcore-setup` is the canonical control repository for project-owned
state.

It stores durable project documentation, execution plans, custom assets,
automation and the canonical coding-agent harness.

`~/azerothcore` remains the upstream-oriented development working tree.

Agent-specific files required inside the AzerothCore checkout may be installed
from the canonical harness, but the installed copies are not the source of
truth.

The upstream `AGENTS.md` and `.agents/` hierarchy are preserved and are not
replaced by private project configuration.

## Alternatives considered

### Store project knowledge inside the AzerothCore checkout

Rejected because it couples private durable state to an upstream working tree
and risks conflicts or accidental commits.

### Store project knowledge in OpenCode sessions

Rejected because sessions and active context are not a reliable long-term
project database.

### Store everything in global OpenCode configuration

Rejected because that would couple project knowledge to a specific tool and
machine configuration.

## Consequences

### Positive

- OpenCode models can be replaced without losing project knowledge.
- OpenCode itself can eventually be replaced.
- The AzerothCore checkout can be recreated.
- Upstream agent instructions remain intact.
- Project history is version controlled independently.

### Negative / trade-offs

- A small installation/bootstrap layer is required.
- Agents must be given controlled access to `~/azerothcore-setup`.
- Documentation discipline is required for long-running work.

## References

- `~/azerothcore/AGENTS.md`
- `~/azerothcore/.agents/`
- `~/azerothcore-setup/docs/project/`
