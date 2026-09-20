---
description: Verify the current AzerothCore task
agent: ac-build
---

Verify the current task against actual project and DEV state.

$ARGUMENTS

Do not stage, commit, push, switch branches, merge, rebase or create a PR.

1. Re-read the active durable plan.

2. Inspect every task-owned tracked and untracked change.

3. Run applicable static checks.

4. For implementation tasks, perform the deepest practical DEV validation.

When relevant, the expected cycle is:

source/config/SQL changes
-> configure/build
-> install
-> database migration/setup
-> stop/restart DEV servers
-> inspect startup/logs
-> automated functional checks
-> runtime/live checks

5. If source code changed:
   - build the appropriate target or project;
   - install when runtime validation requires installed artifacts.

6. If database behavior changed:
   - apply required DEV SQL/migrations;
   - verify resulting schema/data;
   - record database, tables and material mutations in the DEV mutation log.

7. If runtime behavior changed:
   - establish pre-test status;
   - restart when appropriate;
   - verify authserver/worldserver startup;
   - inspect recent and relevant log output;
   - exercise changed behavior as deeply as automation permits.

   If startup fails, fail fast:
   - check lifecycle status;
   - inspect only recent/relevant log output;
   - inspect affected processes and listening ports;
   - perform a small number of evidence-driven diagnostics;
   - retry only when a concrete in-scope correction justifies it;
   - otherwise record FAIL or BLOCKED and stop runtime investigation.

   Do not read complete append-only logs or continue open-ended diagnosis merely
   because startup failed.

8. If client-side or in-game behavior cannot be exercised automatically, mark
it NOT RUN rather than using successful server startup as proof.

9. Record each applicable result as exactly one of:

PASS
FAIL
NOT RUN
NOT APPLICABLE
BLOCKED

10. Delegate independent final inspection to ac-review.

11. Resolve actionable review findings within scope and repeat affected
validation.

12. Update the durable plan with:
   - actions actually executed;
   - observed results;
   - DEV mutation log;
   - remaining limitations;
   - current runtime state.

Leave the task ready for `/finish-task`.
