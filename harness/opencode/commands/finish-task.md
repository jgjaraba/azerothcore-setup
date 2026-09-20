---
description: Complete and archive a durable AzerothCore task
agent: ac-build
---

Finish the current task only after its applicable verification is complete.

$ARGUMENTS

Do not stage, commit, push, switch branches, merge, rebase, create a PR or
modify Git history.

Before completion:

1. Read the complete active durable plan.

2. Compare every involved repository with its recorded baseline.

3. Inspect the complete final task-owned diff, including untracked files.

4. Confirm every claimed validation was actually executed.

5. Confirm database/runtime/build mutations are accurately recorded.

6. Obtain independent ac-review for meaningful implementation or documentation
changes.

7. Resolve or explicitly document every actionable review finding.

8. Update durable project documentation, ADRs and debt/identifier material where
warranted.

9. Record any manual validation still remaining.

10. Move the plan from `plans/active/` to `plans/completed/` only when the task
is genuinely ready for human review.

Then produce the following complete human handoff.

# Human handoff

## Executive summary

Explain:
- original problem/goal;
- implemented solution;
- final task state.

## Scope and baseline

For every involved repository report:
- repository path;
- writable/read-only status;
- branch;
- initial HEAD;
- initial working-tree state.

State explicitly what was outside scope.

## Investigation / root cause

Report:
- relevant findings;
- root cause when applicable;
- primary evidence;
- meaningful hypotheses rejected.

Use VERIFIED / INFERRED / UNKNOWN where the distinction matters.

## Design

Explain:
- selected design;
- why it was selected;
- meaningful alternatives considered;
- important trade-offs.

## Implementation

Report:
- every task-owned file changed;
- material changes by component;
- API/hook/config/schema/identifier changes;
- compatibility/update implications.

Do not merely repeat a filename list.

## Database changes

For every database touched report:
- database name;
- tables affected;
- SQL/migrations executed;
- material ad-hoc SQL executed;
- destructive/reconstructive operations;
- temporary data created/removed;
- useful before/after observations;
- state left applied;
- rollback/recreation method.

If no database mutation occurred, state NOT APPLICABLE.

## Build and installation

Report:
- configure/build mechanism;
- relevant targets/options;
- build result;
- install result;
- install prefix;
- whether installed binaries/runtime artifacts correspond to the current
  working tree.

## Runtime validation

Report:
- initial server state when known;
- stop/start/restart actions;
- authserver result;
- worldserver result;
- relevant startup warnings/errors;
- logs inspected;
- actual runtime functionality exercised.

Successful startup alone is not functional feature validation.

## Validation matrix

Use only:

PASS
FAIL
NOT RUN
NOT APPLICABLE
BLOCKED

Include at least:

| Validation | Status | Evidence / notes |
|---|---|---|
| Static/diff checks | ... | ... |
| Build | ... | ... |
| Install | ... | ... |
| Database migration/state | ... | ... |
| authserver startup | ... | ... |
| worldserver startup | ... | ... |
| Automated functional checks | ... | ... |
| In-game validation | ... | ... |
| Client/server compatibility | ... | ... |
| Independent review | ... | ... |
| Rollback documented | ... | ... |

Add task-specific rows where useful.

## Independent review

Report:
- reviewer used;
- review scope;
- findings;
- fixes performed;
- deliberately deferred findings and rationale.

## DEV environment mutation log

Provide a chronological summary of material mutations:
- configure/build/install operations;
- runtime artifacts changed;
- runtime configuration changes;
- database mutations;
- temporary test state;
- process stop/start/restart/kill operations.

Do not include trivial read-only commands.

## Final DEV state

Report explicitly:

- authserver: RUNNING / STOPPED / UNKNOWN
- worldserver: RUNNING / STOPPED / UNKNOWN
- feature SQL/migrations currently applied: yes/no/details
- temporary test data remaining: yes/no/details
- installed binaries correspond to current task working tree:
  YES / NO / UNKNOWN
- runtime configuration changed: yes/no/details
- DBC/client state changed: yes/no/details

### Snapshot recommendation

Choose and explain exactly one:

- KEEP CURRENT VM STATE
- RESTORE PRE-TASK SNAPSHOT BEFORE UNRELATED WORK
- EITHER IS SAFE
- UNKNOWN / MANUAL DECISION REQUIRED

## Risks and limitations

Explain:
- behavior not demonstrated;
- update-sensitive code/data;
- unresolved assumptions;
- compatibility risks;
- manual/in-game validation still needed.

## Rollback

Explain concretely how to recover or revert:
- source changes;
- database changes;
- runtime configuration;
- installed artifacts;
- client/DBC changes.

The VM snapshot may be the catastrophic rollback mechanism, but identify
task-level rollback where one exists.

## Documentation

List:
- component docs updated;
- ADRs created/updated;
- identifier/debt registry changes;
- completed plan.

Explain what durable project knowledge was added.

## Human review checklist

Tell the user:
- repositories containing task-owned changes;
- diffs deserving particular attention;
- manual/in-game validation still pending;
- DEV state they should know about;
- any action advisable before commit.

## Git handoff

For every writable repository report:
- path;
- current branch;
- initial HEAD;
- current HEAD;
- task-owned changed files;
- pre-existing changes preserved.

Then explicitly report:

- staged: yes/no
- committed: yes/no
- pushed: yes/no
- PR created: yes/no

Under normal project policy all four must be `no`.

End with a concise statement of whether the working tree is ready for human
review.

Do not make the commit/publication decision for the user.
