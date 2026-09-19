# Architectural Decision Records

Use an ADR for decisions that should remain understandable after the original
task or conversation has disappeared.

Examples include:

- choosing database customization versus a module or core modification;
- assigning durable custom ID ranges;
- establishing compatibility or update policies;
- selecting a long-term integration strategy;
- intentionally accepting an architectural trade-off.

## Naming

Use:

`ADR-NNNN-short-description.md`

Example:

`ADR-0001-project-knowledge-lives-in-azerothcore-setup.md`

## Lifecycle

Recommended statuses:

- Proposed
- Accepted
- Superseded
- Deprecated

Do not silently rewrite historical decisions when the architecture changes.

Create a new ADR and mark the previous one as superseded.
