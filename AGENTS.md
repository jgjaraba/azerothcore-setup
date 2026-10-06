# Project instructions

## Project identity

`azerothcore-setup` is the private control repository for the custom AzerothCore
server. The project spans two equally important roots:

- `/home/dev/azerothcore-setup` — project assets, SQL, client data, scripts and
  durable documentation.
- `/home/dev/azerothcore` — AzerothCore source, modules and DEV runtime.

OpenCode runs from `azerothcore-setup`; agents may work in either root as the
task requires.

## Durable knowledge

The persistent knowledge base is `/home/dev/azerothcore-setup/docs/project/`.
Start with [`docs/project/README.md`](docs/project/README.md), then read only
the relevant documents. Live repository and DEV state is authoritative for
transient facts. Add verified, durable knowledge only when it would materially
help future work. Documentation is curated knowledge, not an execution log.

## Autonomy and change strategy

This is a disposable DEV environment. Resolve normal technical decisions
autonomously. Do not request approval for routine inspection, editing, builds,
tests, SQL, runtime management, package tooling, Git working-tree operations or
similar development work.

Ask the user only when an actual product/design requirement is unknowable from
the task, repositories, documentation, environment, research or reasonable
engineering judgment.

Prefer the least invasive correct solution, approximately:

```text
configuration/data -> SQL -> module -> core modification
```

This is a maintainability preference, not a restriction. Correctness takes
precedence.

## Validation and review

Never claim a build, test, in-game behavior or verification unless it was
actually performed. Use `ac-review` for independent review of meaningful
changes.

## AzerothCore instructions

Before substantive changes under `/home/dev/azerothcore`, read
`/home/dev/azerothcore/AGENTS.md` and applicable nested `AGENTS.md` files.
Those instructions apply inside AzerothCore but do not override private project
rules.

## Preserve work and Git

Preserve unrelated user work where practical. Inspect repository status before
editing and do not revert or clean changes you did not make.

**Never create a Git commit. Never push.**
