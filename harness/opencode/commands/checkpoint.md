---
description: Checkpoint a durable AzerothCore task
agent: ac-build
---

Checkpoint the current task.

$ARGUMENTS

Do not stage, commit, push, switch branches, merge, rebase or alter Git history.

Update the active durable plan with:

- current task mode;
- repositories and branches;
- initial/current HEADs;
- task-owned changed files;
- preserved pre-existing changes;
- implementation/research completed;
- important evidence discovered;
- database mutations performed;
- build/install operations performed;
- runtime/configuration mutations performed;
- current authserver/worldserver state when relevant;
- validation completed with PASS/FAIL/NOT RUN/NOT APPLICABLE/BLOCKED;
- unresolved review findings;
- risks/open questions;
- exact next action.

The checkpoint must contain enough information for another session to continue
without relying on hidden conversation state.
