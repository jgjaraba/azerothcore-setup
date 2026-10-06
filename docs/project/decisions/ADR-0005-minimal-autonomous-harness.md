# ADR-0005: Minimal autonomous agent harness with a curated knowledge base

Status: Superseded by ADR-0006
Date: 2026-10-02

## Context

The original harness modelled the agent as a process operator rather than an
engineer. It required a durable per-task plan file, a generated environment
snapshot refreshed before every task, a five-command task lifecycle
(`start-task`, `resume-task`, `checkpoint`, `verify`, `finish-task`), a fourth
`ac-architecture` agent, and a permission policy that converted ordinary work
— editing, shell redirection, SQL, builds, `sudo`, Git inspection, branch and
working-tree operations — into approval prompts.

That structure existed because the environment was treated as fragile. It is
not: this is a disposable development VM protected by external snapshots. The
process machinery cost more than it produced. It duplicated live facts in
committed documents that immediately went stale, forced the agent to maintain
an execution log instead of learning anything, and put a human in the loop for
decisions an agent is better equipped to make from evidence.

## Decision

The harness is three agents and one knowledge base.

- `ac-build` is the primary autonomous implementation and orchestration agent.
  It owns a task from request to validated implementation and may freely
  inspect, edit, research, compile, install, test, mutate DEV databases, drive
  the DEV runtime, use `sudo`, and perform normal Git operations.
- `ac-research` is the research specialist.
- `ac-review` is the independent reviewer.

There are no task commands, no plans hierarchy, no environment snapshot script,
and no `ac-architecture` agent. Durable project knowledge lives in
`docs/project/`, indexed by `docs/project/README.md`, and agents grow it when
they verify something worth keeping.

The project's own permission contribution is a single allow-all rule plus hard
denies for `git commit` and `git push`. The catch-all rule is written first so
the specific denies match last, because OpenCode resolves the last matching
rule. The denies cover the bare form and the `git -C <path>`, `git -c <k=v>`,
`git --<flag>`, `<path>/git` and `sudo … git` spellings, each in a bare and an
argument form.

Four `allow` entries also appear before the denies (`sudo`, `sudo *`,
`git reset --hard*`, `git clean -fd*`). They look redundant under the
catch-all, but they are not: OpenCode deep-merges the user's global
`~/.config/opencode/opencode.jsonc`, which asks for those commands. Re-declaring
them here overrides the inherited ask, because the project scope is merged last.

The project cannot control everything the merged policy contains. The user's
global config currently contributes two `ask` rules for `ssh *` and `scp *`.
Those are the machine owner's defaults, outside this repository, and the project
neither declares nor relaxes them.

Two limitations are accepted deliberately:

- **Wrappers fall through.** Deny patterns are anchored on the command string,
  so `cd <dir> && git commit` and `env git push` still match the catch-all.
  Widening to `* git commit*` would also block legitimate searches such as
  `rg "git commit" docs` in a knowledge base that documents its own history.
- **The denies can over-match.** Because a prefix pattern spans the rest of the
  command, a read-only command that merely mentions the word, such as
  `git -C <path> log --grep commit --oneline`, can be denied. A false denial is
  recoverable by rewording the command; a missed commit is not, so the bias is
  deliberate.

The durable defense is the instruction in every agent prompt and in
`project-instructions.md`.

Agents must never create a commit and never push; the user owns history and
publication.

`docs/project/generated/` and `scripts/agent/refresh-environment.sh` are gone.
Transient facts are read from the live repositories and the live machine.

## Alternatives considered

### Keep the task lifecycle and plans

Rejected. A durable plan duplicates information the agent already has, adds a
mandatory artifact to every task, and turns the knowledge base into a history
of work rather than a body of knowledge. Live state is authoritative anyway.

### Keep `ac-architecture` as a separate decision agent

Rejected. Its concern — maintainability, update safety, database versus module
versus core — is already a first-class part of `ac-build`'s mandate, and
`ac-review` covers it independently. A fourth agent added a delegation hop
without adding capability.

### Keep the read-only sandbox for research and review

Rejected. Specialization belongs in the role prompt. Denying edit and shell to
research and review made them unable to verify a claim empirically, which
reduced the quality of exactly the output they exist to produce.

### Keep per-command allowlists and approval prompts

Rejected. In a disposable DEV VM an approval prompt is pure friction. It was
also incomplete: the deny list grew entries while the allow list silently
shadowed them, so the policy's real effect was hard to predict.

### Keep an approved feature-branch ceremony

Rejected. Requiring a human-prepared branch before any edit blocked autonomous
work for no safety benefit in a throwaway environment. `ac-build` now branches
itself.

## Consequences

### Positive

- Work flows from request to validated implementation without ceremony.
- Only two real prohibitions remain, and both are enforced mechanically for the
  command forms listed above.
- `docs/project/` is curated knowledge: architecture, components, features,
  ADRs, identifiers, debt and durable learnings.
- Fewer artifacts to install, validate and keep in sync.

### Negative / trade-offs

- There is no cross-session resumption artifact. Continuity depends on
  `docs/project/` plus the user's branch and commits.
- `ac-review` and `ac-research` can modify state if they choose; only their role
  prompts hold them to reading and reporting.
- Nothing records what happened during a session. That is deliberate, and it
  means a task whose only outcome was a transient fix leaves no trace.

## References

- Historical implementation: the former `harness/opencode/` tree and
  `scripts/agent/install-harness.sh` (removed by ADR-0006).
- `docs/project/README.md`
- `scripts/agent/validate-opencode.sh`
- ADR-0001: Keep durable project knowledge outside the AzerothCore checkout
