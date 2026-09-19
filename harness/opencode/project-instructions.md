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

## Inspection tool policy

For read-only repository and source inspection, prefer OpenCode's structured
read, glob, grep and directory-listing tools over Bash.

Avoid Bash loops, `find`, arbitrary Python one-liners, `cat`, or `sed` merely
to enumerate or read project files when structured tools can perform the same
operation.

Small read-only shell commands and pipelines using allowlisted inspection tools
such as Git, `rg`, `grep`, `printf`, `sort`, `wc`, or version queries are
acceptable when they are clearer or more efficient.

Prefer the generated environment state and direct read-only Git commands for
multi-repository state inspection.

Use Bash when command execution semantics are actually required, such as Git
state inspection, builds, tests, database operations, trusted project scripts,
or other explicit execution tasks.

Do not use Bash redirection, Python, or other shell mechanisms to bypass edit
or permission boundaries.

Commands that can modify repository state, databases, runtime configuration,
installed files, system packages, or processes should remain subject to the
configured approval policy.

## Project path discipline

The known project roots are:

- `/home/dev/azerothcore`
- `/home/dev/azerothcore-setup`

For project discovery and inspection, stay inside those explicit roots.

Do not run glob, grep, list, read, `find`, or similar discovery operations
rooted at `~`, `/home/dev`, or another parent directory merely to locate
project files.

Do not search the whole home directory for a file whose project path is already
known or can be derived from the generated environment state or project
documentation.

Use:

- the current AzerothCore workspace for core/module paths;
- `/home/dev/azerothcore-setup` for private project assets;
- `docs/project/generated/ENVIRONMENT.md` for repository/module discovery.

Request broader external-directory access only when the task genuinely requires
a resource outside these project roots.

## Feature branch and publication policy

Implementation work is performed only on user-created feature branches.

The user owns repository and publication operations.

At task startup:

- inspect the current branch, HEAD and working-tree state of every repository
  that may be modified;
- record the relevant repository baselines in the durable execution plan;
- do not create, switch, rename, delete, merge or rebase branches;
- do not modify an implementation repository while it is on its protected/base
  branch;
- identify and preserve all pre-existing working-tree changes.

For multi-repository tasks, each repository that will receive task-owned changes
must already be on an appropriate user-created feature branch.

The `azerothcore-setup` repository is also part of this rule whenever the task
creates or modifies durable plans, project documentation, scripts, SQL or other
project-owned assets there.

The agent must not:

- stage files;
- create commits;
- push;
- open or merge pull requests;
- modify Git history.

At task completion, provide a human handoff containing:

- every repository modified;
- the current branch of each repository;
- task-owned files changed;
- pre-existing changes preserved;
- validation actually performed;
- remaining validation or in-game testing;
- confirmation that no staging, commit, push or PR was performed.

Leave the working trees ready for human inspection and commit.
