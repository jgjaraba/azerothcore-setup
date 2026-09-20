---
description: Start a durable private AzerothCore task
agent: ac-build
---

Start the following task:

$ARGUMENTS

Before substantial work:

1. Regenerate the project environment state.

2. Read:
   - the project knowledge index;
   - only project/component documentation relevant to this task;
   - relevant accepted ADRs;
   - relevant technical-debt entries.

3. Classify the task as exactly one mode:
   - implementation;
   - research/documentation;
   - audit/read-only.

4. Determine repository scope.

For every relevant repository record:
- path;
- writable or read-only;
- current branch;
- initial HEAD;
- initial working-tree state.

A writable repository must already be on a user-created feature branch.

Do not create or switch branches.

If a writable repository is unexpectedly on a protected/base branch, stop
before mutation and report BLOCKED.

5. Preserve pre-existing dirty state and distinguish it from task-owned changes.

6. For implementation tasks, inspect the relevant initial DEV state when useful:
   - authserver/worldserver status;
   - database/schema/data baseline;
   - runtime configuration;
   - build/install baseline.

Do not collect unrelated state mechanically.

7. For non-trivial work create a durable execution plan under:

    ~/azerothcore-setup/plans/active/

using:

    ~/azerothcore-setup/plans/TEMPLATE.md

The plan must record:

- task mode;
- goal;
- scope;
- repository baselines;
- verified technical baseline;
- constraints;
- implementation/research strategy;
- validation strategy;
- DEV mutation log;
- risks/open questions;
- next exact action.

8. Respect relevant upstream AGENTS.md and repository-specific instructions.

9. Delegate evidence gathering to ac-research where useful.
Use ac-architecture for meaningful design/update-safety decisions.
Use ac-review after a stable implementation/documentation state exists.

For implementation tasks, after planning you may autonomously modify and
exercise the authorized DEV environment according to project policy.

For research/documentation or audit/read-only tasks, remain read-only except
for explicitly authorized documentation/plan paths.
