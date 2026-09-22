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

For implementation tasks, database, build, runtime, installed-file and
process mutations inside the authorized disposable DEV VM may execute
autonomously according to the policy below.

Research/documentation and audit/read-only tasks remain read-only unless their
explicit scope says otherwise.

Do not use shell wrappers, scripting languages, environment indirection or
other mechanisms to bypass a configured permission boundary.

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

## Autonomous DEV execution policy

This machine is a disposable AzerothCore development VM protected by external
snapshots.

For implementation tasks, optimize for complete end-to-end validation rather
than preserving the initial DEV runtime state.

### Task modes

Every task must identify exactly one execution mode in its durable plan:

- `implementation`;
- `research/documentation`;
- `audit/read-only`.

Research/documentation and audit/read-only tasks remain read-only unless their
explicit task scope authorizes a particular mutation.

### Authorized DEV boundary

The local development boundary consists of:

- `/home/dev/azerothcore`;
- `/home/dev/azerothcore/modules/*`;
- `/home/dev/azerothcore-setup`;
- `/home/dev/azerothcore/env/dist`;
- local databases:
  - `acore_auth`;
  - `acore_characters`;
  - `acore_world`;
  - `acore_playerbots`.

Production systems must never be discovered or accessed.

Do not remotely administer or copy project state to another machine through
SSH, SCP, SFTP, rsync or equivalent mechanisms.

Do not connect MySQL tooling to a remote host.

### Repository write boundary

A repository may receive implementation changes only when:

- the task explicitly includes it in writable scope; and
- the user has already placed it on the intended feature branch.

Before mutation, record:

- repository path;
- branch;
- initial HEAD;
- initial working-tree state.

If a repository intended for modification is unexpectedly on a protected/base
branch, stop before modifying it and report `BLOCKED`.

Preserve pre-existing working-tree changes.

The human owns branch management, staging, history and publication.

The agent must not:

- create, switch, rename or delete branches;
- stage changes;
- commit;
- push or pull;
- merge or rebase;
- cherry-pick or revert;
- reset or clean repositories;
- create or merge pull requests.

### Implementation freedom

Within the authorized scope of an implementation task, `ac-build` may
autonomously:

- edit source and project-owned files;
- edit effective DEV configuration;
- modify `/home/dev/azerothcore/env/dist`;
- configure and regenerate the build;
- compile core and modules;
- install build outputs;
- execute local MySQL queries and migrations;
- insert, update and delete DEV data;
- create, alter, truncate or drop DEV tables when technically justified;
- create and restore DEV database dumps;
- create and remove temporary test data/files;
- start, stop and restart authserver/worldserver;
- use normal user-level process control when needed;
- inspect logs;
- repeat implementation and validation cycles.

The VM is disposable. Restoring the original runtime/database state at task end
is not mandatory unless the task requires it.

Changes must nevertheless be deliberate and related to the active task.

### Database policy

Database mutations are authorized only against:

- `acore_auth`;
- `acore_characters`;
- `acore_world`;
- `acore_playerbots`.

Use the configured local DEV login path and never expose credentials, tokens,
passwords or connection strings.

Prefer version-controlled SQL or module migrations for durable changes.

Ad-hoc SQL is acceptable for investigation and validation. Record material SQL
mutations and whether their resulting state remains at handoff.

The VM snapshot is the catastrophic rollback mechanism. A database dump is
optional when it materially improves debugging or task-level rollback; do not
create backups mechanically before every disposable mutation.

### Build and installation policy

Implementation tasks may configure, build, rebuild and install autonomously.

Use the actual build/install layout verified from current project state rather
than relying on stale assumptions.

Static-module source changes require compatible rebuild/install before runtime
validation.

Successful compilation is not runtime validation.

### Runtime policy

Prefer the tracked local lifecycle scripts when appropriate:

- `/home/dev/azerothcore-setup/scripts/start.sh`;
- `/home/dev/azerothcore-setup/scripts/status.sh`;
- `/home/dev/azerothcore-setup/scripts/stop.sh`.

Direct user-level process control is allowed when required to debug or recover
a stuck DEV process.

System-wide service management and sudo remain explicit human approval
boundaries.

Successful server startup is not functional feature validation.

### Delegated subagents

`ac-research`, `ac-architecture` and `ac-review` remain read-only evidence and
review agents.

They must not:

- modify files;
- mutate databases;
- build/install;
- modify runtime state;
- start/stop processes;
- mutate Git state.

`ac-build` owns implementation and DEV execution.

### Runtime failure diagnosis

Runtime validation must fail fast.

If a lifecycle startup command such as `start.sh` fails:

1. check the resulting lifecycle status;
2. inspect only recent and relevant portions of the affected logs;
3. inspect the relevant process state and listening ports;
4. perform a small number of targeted diagnostics based on concrete evidence;
5. either correct an in-scope DEV problem and retry deliberately, or report
   `FAIL` / `BLOCKED`.

Do not enter an open-ended investigation loop after a failed startup.

Prefer recent log windows, timestamps, or output produced by the current
invocation over reading complete append-only historical log files.

Historical log lines must not be treated as evidence of the current process
state without corroboration from current status, PID, socket, or timestamp
evidence.

### Validation vocabulary

Every reported validation item must use one of:

- `PASS`;
- `FAIL`;
- `NOT RUN`;
- `NOT APPLICABLE`;
- `BLOCKED`.

`PASS` requires actual execution or direct observation.

Never convert an unexecuted check into an implied success.

### DEV mutation log

For implementation tasks maintain a chronological durable record of material
environment mutations, including:

- configure/build/install operations;
- runtime artifacts changed;
- effective configuration changes;
- database migrations and ad-hoc mutation SQL;
- destructive/reconstructive database operations;
- temporary test state;
- server stop/start/restart actions;
- unusual process manipulation.

The final handoff must describe the resulting DEV state and whether restoring
the pre-task VM snapshot is advisable before unrelated development.

<!-- ENGINEERING_AUTONOMY_POLICY_BEGIN -->

## Engineering Autonomy and Stop Policy

Agents are expected to work autonomously inside the already-approved DEV scope.

The default workflow is:

`inspect -> infer from evidence -> implement -> validate -> review -> fix -> checkpoint`

Do NOT use:

`inspect -> encounter minor uncertainty -> stop for human input`

### Routine technical uncertainty is not a blocker

The following MUST normally be resolved autonomously:

- unknown, renamed, or stale SQL column assumptions;
- failed read-only SELECT, SHOW, or DESCRIBE queries;
- differences between expected and actual table schemas;
- locating the correct creature/gameobject/template identifier column;
- resolving effective creature or gameobject loot-template IDs;
- locating the correct AzerothCore table for an already-approved behavior;
- SQL syntax errors;
- SQL codestyle failures;
- manifest ordering;
- project-owned duplicate data;
- condition-key corrections;
- locale-table mapping;
- DBC record-layout inspection;
- selecting between technically equivalent safe implementations;
- ordinary review findings that do not alter approved gameplay or narrative.

For routine schema uncertainty:

1. use `DESCRIBE` or `SHOW CREATE TABLE`;
2. inspect nearby canonical database rows;
3. inspect AzerothCore source when semantics remain unclear;
4. correct the query or implementation;
5. retry;
6. continue the current task.

A failed query is evidence to investigate, not a reason to stop.

### Automatic recovery loop

When a routine command fails:

1. classify the failure;
2. inspect actual repository/schema/runtime state;
3. correct the assumption;
4. retry the operation;
5. continue.

Examples:

`Unknown column`
-> `DESCRIBE`
-> use the actual column
-> continue.

Unexpected loot reference
-> inspect `creature_template` / `gameobject_template` and canonical rows
-> resolve effective loot template
-> continue.

Condition insertion failure
-> inspect the `conditions` schema and canonical examples
-> correct source keys
-> continue.

Do not escalate these situations to the human.

### Current evidence overrides stale assumptions

Never preserve an earlier schema assumption when current DEV evidence contradicts it.

The current repository, current DEV schema, and inspected AzerothCore source are authoritative.

Correcting a stale assumption is ordinary engineering work.

### Human escalation threshold

Ask the human only when at least one of these applies:

#### Narrative or gameplay choice

- materially different story direction;
- progression or balance change;
- solo/group design change.

#### Major architecture deviation

- new AzerothCore core C++ modification;
- Individual Progression modification;
- Playerbots modification;
- modification of another module;
- new custom client models/textures/assets;
- fundamental deviation from the approved behavior.

#### Risk boundary

- production mutation;
- destructive or unbounded modification outside project-owned data;
- credentials or secrets;
- unrelated user changes.

#### Genuine contradiction

Verified evidence proves the approved behavior cannot be implemented safely or correctly without changing its intended design.

Everything else should normally be resolved autonomously.

### Do not manufacture human decisions

When evidence clearly favors one safe solution, choose it.

When several implementations are technically equivalent, choose the simplest and most update-safe one.

When a previous assumption is wrong, correct it.

When a weak implementation detail is unnecessary, remove or replace it within the approved behavior.

Do not ask the human merely to approve routine engineering work.

### Execution-window behavior

If execution/tool budget becomes constrained:

- finish the smallest coherent stage;
- validate completed work;
- checkpoint durable state;
- set an exact `Next exact action`;
- stop cleanly.

Do not abandon already-authorized work merely because the entire task does not fit into one response.

A trivially recoverable query or schema error is not a valid early stop.

### Approved DEV autonomy

Within an already-authorized task agents may:

- inspect schemas and source;
- correct failed queries;
- modify project files;
- apply project-owned SQL to DEV;
- reapply SQL for idempotency validation;
- generate permitted DBC records;
- install server-side generated DEV assets;
- restart DEV services;
- inspect logs;
- delegate review;
- fix ordinary review findings;
- update durable task state.

Task-specific restrictions still apply.

Production remains forbidden unless explicitly authorized.

Commit, push, merge, and rebase remain forbidden unless explicitly authorized.

### Core principle

**Uncertainty requires investigation, not human escalation.**

**A failed query is evidence to inspect, not a reason to stop.**

**Do not manufacture a human decision where none exists.**

<!-- ENGINEERING_AUTONOMY_POLICY_END -->
