# AzerothCore project knowledge

This directory is the persistent knowledge base for the private AzerothCore
project. It is the durable memory of the work: it must remain useful to any
future agent or human regardless of session, model, tool or conversation.

Start here. Read this file, then read only the documents relevant to the task in
hand.

## Source-of-truth order

1. The live repositories and the live DEV environment for anything measurable —
   current branches, revisions, dirty files, installed module revisions,
   database contents, running processes, effective configuration, installed
   artifacts. Inspect them directly.
2. Durable project knowledge in this directory, including accepted ADRs.
3. The current task requirements.

If two sources disagree, investigate the discrepancy rather than assuming the
documentation is right. Conversation history is not a source of project state.

## What to store here

Store:

- verified project architecture;
- custom behaviour and custom-content design contracts;
- non-obvious AzerothCore, module and client findings;
- ID and range conventions;
- implementation conventions;
- important compatibility findings;
- reusable operational knowledge (`LEARNINGS.md`);
- architectural decisions (`decisions/`);
- known limitations and deliberate trade-offs (`debt/`).

Do not store:

- task progress or plans;
- temporary errors or an execution log;
- command transcripts;
- current Git status, branches or commit hashes;
- facts that any tool can trivially reconstruct.

Documentation is curated knowledge. If a document grows a chronology, it has
become a log and belongs somewhere else — or nowhere.

When durable information changes, update the document that already owns that
subject instead of adding a contradictory note elsewhere. Create a new document
only when the body of knowledge justifies it.

## Index

### Start here

| Document | Use it for |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Repository roles, the integration chain, reproducibility and operational boundaries |
| [`LEARNINGS.md`](LEARNINGS.md) | Verified gotchas, symptom → cause → check entries that are expensive to rediscover |

### Components

[`components/README.md`](components/README.md) — what belongs in a component
document and when to create one.

| Document | Covers |
|---|---|
| [`components/runtime.md`](components/runtime.md) | Build/install layout, configuration ownership, lifecycle scripts, deployment state |
| [`components/data-and-database.md`](components/data-and-database.md) | DEV database topology, the custom world SQL manifest and its install order |
| [`components/modules.md`](components/modules.md) | Installed module catalog, relationship index, per-module compatibility notes |
| [`components/playerbots-ecosystem.md`](components/playerbots-ecosystem.md) | The coordinated Playerbots / Individual Progression / Character Services / Dungeon Clear / MultiBot Bridge unit |
| [`components/custom-world-sql.md`](components/custom-world-sql.md) | Verified behavior of the project-owned world SQL, dependencies and update concerns |
| [`components/client-assets.md`](components/client-assets.md) | DBC resources, client MPQ patches, addons and the server/client data contract |

### Features

[`features/README.md`](features/README.md) — feature documents are design
contracts, not task logs.

| Document | Covers |
|---|---|
| [`features/forsaken-paladin-class-quests.md`](features/forsaken-paladin-class-quests.md) | The Undead Paladin quest chains, item/DBC contract and loot conditions |

### Decisions and risk

| Document | Use it for |
|---|---|
| [`decisions/README.md`](decisions/README.md) | How to write an ADR: naming, lifecycle, and when a decision deserves one |
| [`decisions/TEMPLATE.md`](decisions/TEMPLATE.md) | Starting point for a new ADR |
| [`debt/README.md`](debt/README.md) | When something belongs in the debt register |
| [`debt/REGISTER.md`](debt/REGISTER.md) | Known durable risks, each with an action trigger |
| [`CUSTOM-IDENTIFIERS.md`](CUSTOM-IDENTIFIERS.md) | Evidence-backed inventory of project identifiers and the collision-check rule for new allocations |

## Related material outside this directory

- `~/azerothcore-setup/docs/` — operational and feature-specific guides that
  predate this knowledge base (NPC creation, new currency mechanics, custom
  content inventory, MorphSummon sources).
- `~/azerothcore-setup/patches/` — version-controlled core source patches
  (see `decisions/ADR-0003-core-source-patches.md`).
- `~/azerothcore/AGENTS.md` and `~/azerothcore/.agents/` — upstream AzerothCore
  instructions, which remain authoritative for core conventions.

## Evidence vocabulary

Use these words when the distinction matters:

- **VERIFIED** — the umbrella term for anything established below. Say which
  kind of verification you mean when it matters.
- **TRACKED** — directly represented by version-controlled source, SQL,
  templates, scripts, or an accepted ADR. Does not prove deployment.
- **OBSERVED** — measured from the current checkout, build/install tree,
  effective runtime configuration, or DEV database. Does not prove intent,
  reproducibility, or gameplay correctness. Date it, because deployment drifts.
- **VALIDATED** — behavior demonstrated by a recorded build, test, or live-stack
  scenario against a stated baseline.
- **INFERRED** — strongly suggested by evidence but not directly established.
  State its basis; do not present it as project fact.
- **UNKNOWN** — an important fact not established by available evidence.
