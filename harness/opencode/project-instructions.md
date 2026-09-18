# Private AzerothCore Project Instructions

These instructions complement the upstream AzerothCore `AGENTS.md`.

The upstream `AGENTS.md` and `.agents/` hierarchy remain authoritative for
AzerothCore coding conventions, review rules, SQL conventions and upstream
development practices.

Private project knowledge lives in:

`~/azerothcore-setup`

Conversation history is not an authoritative source of project state.

Global OpenCode configuration and global instruction files are machine/user
defaults only.

They must not be used as authoritative sources for project-specific facts.
Project-specific state must come from the current repositories, generated
environment state and durable project documentation.

## Mandatory startup protocol

Before substantial work:

1. Run:

   `~/azerothcore-setup/scripts/agent/refresh-environment.sh`

2. Read:

   `~/azerothcore-setup/docs/project/README.md`

3. Read:

   `~/azerothcore-setup/docs/project/generated/ENVIRONMENT.md`

4. Check:

   `~/azerothcore-setup/plans/active/`

   for a relevant durable execution plan.

5. Read only the project component documentation relevant to the task.

6. Inspect the current Git status and diff before making assumptions about
   pending work.

Never rely on a remembered repository commit, module version or dirty state
when it can be verified directly.

## Two planning layers

AzerothCore upstream may require temporary implementation plans under:

`.agents/plans/`

Follow that upstream convention when applicable.

Durable cross-session project state belongs under:

`~/azerothcore-setup/plans/active/`

These serve different purposes.

`.agents/plans/` is upstream task workspace.

`~/azerothcore-setup/plans/active/` is durable continuity state that must allow
a new session or different model to resume work without the previous
conversation.

## Durable task state

For non-trivial private project work, maintain one active plan.

After meaningful milestones record:

- verified findings;
- decisions;
- implementation changes;
- validation actually performed;
- unresolved issues;
- the next exact action.

Do not store conversation transcripts, hidden reasoning or speculative notes as
facts.

## Project knowledge

Durable architecture and verified subsystem behaviour belong under:

`~/azerothcore-setup/docs/project/`

Long-lived architectural decisions belong under:

`~/azerothcore-setup/docs/project/decisions/`

Facts that can be reconstructed automatically belong in generated state rather
than manually maintained documentation.

## Change strategy

When multiple technically correct approaches exist, prefer:

1. database-only customization;
2. AzerothCore module;
3. core modification.

This is a maintainability preference, not an absolute rule.

Correctness and compatibility take precedence.

## azerothcore-setup safety

The setup repository may contain unrelated pending work.

Never modify, stage, revert or clean unrelated files.

In particular, do not assume existing SQL changes belong to the current task.

## Validation

Never claim that something builds, passes tests, works in-game or has been
verified unless that validation was actually performed.

Before considering implementation complete:

- inspect the final diff;
- run the relevant validation;
- update the durable execution plan;
- invoke independent review for meaningful changes.

## Environment boundary

This is a development and validation environment.

Never modify production systems implicitly.

Never push Git changes automatically.
