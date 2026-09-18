---
description: Persist durable state for the current AzerothCore task
agent: ac-build
---

Checkpoint the current task.

Update its durable active execution plan with only information needed by a
fresh future session:

- verified findings;
- decisions;
- implementation changes;
- validation actually performed;
- unresolved issues;
- next exact action.

Do not store conversation transcripts, chain-of-thought or temporary
speculation.

Update component documentation or an ADR only when durable project knowledge
has actually changed.
