---
description: Resume a durable AzerothCore task
agent: ac-build
---

Resume the current durable task.

$ARGUMENTS

1. Regenerate project environment state.

2. Read the relevant active plan completely.

3. Read only the project/component documentation needed for the next action.

4. Compare current repository state with the baseline recorded in the plan:
   - branch;
   - HEAD;
   - working tree;
   - task-owned changes;
   - pre-existing changes.

Do not create or switch branches.

If repository state unexpectedly diverged from the plan, stop before mutation
and explain the mismatch.

5. For implementation tasks, inspect current DEV runtime/database state where
needed to establish whether previous task mutations remain applied.

Do not assume that the VM was left exactly as a previous session reported.

6. Continue from the plan's `Next exact action`.

7. Keep the DEV mutation log and validation state current.

Do not stage, commit, push, create a PR or alter Git history.
