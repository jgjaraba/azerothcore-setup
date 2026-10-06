# Components

One document should describe each project subsystem whose durable behavior,
customizations or constraints are important to future work.

| Document | Covers |
|---|---|
| [`runtime.md`](runtime.md) | Build/install layout, configuration ownership, lifecycle scripts, deployment state |
| [`data-and-database.md`](data-and-database.md) | DEV database topology, the custom world SQL manifest and its install order |
| [`modules.md`](modules.md) | Installed module catalog, relationship index, per-module compatibility notes |
| [`playerbots-ecosystem.md`](playerbots-ecosystem.md) | The coordinated Playerbots / Individual Progression / Character Services / Dungeon Clear / MultiBot Bridge unit |
| [`custom-world-sql.md`](custom-world-sql.md) | Verified behavior of the project-owned world SQL, dependencies and update concerns |
| [`client-assets.md`](client-assets.md) | DBC resources, client MPQ patches, addons and the server/client data contract |

The module catalog and the focused Playerbots ecosystem / custom world SQL
documents reflect a source-level audit performed on 2026-09-19.

Feature design contracts live in [`../features/`](../features/). Cross-component
identifier ownership is documented in [`../CUSTOM-IDENTIFIERS.md`](../CUSTOM-IDENTIFIERS.md);
durable risks are recorded in [`../debt/REGISTER.md`](../debt/REGISTER.md).

Do not create speculative component documentation. Update the document that
already owns a subject instead.
