# Database and custom data

## Database configuration boundary

The local authserver and worldserver configuration files define login, world,
and character database connections. Their connection values are local ignored
runtime configuration and are intentionally not duplicated in project
documentation.

## DEV database topology

**OBSERVED (2026-09-20, read-only local DEV queries).** The configured local
login path reached four databases: `acore_auth`, `acore_characters`,
`acore_world`, and `acore_playerbots`. The world `version` row identifies the
local core revision and `ACDB 335.17-dev`; the current revision is a fact to
read from the database or the repository on demand, not durable semantic
documentation.

Playerbots is a first-class fourth database dependency. Its module repository
contains creation/grant and update SQL, and the observed database has its own
`updates` and `updates_include` tables plus bot, travel, cache, and text data.
Its `version_db_playerbots` table was empty while its `updates` table had rows.
The module actively queries the former for the displayed Playerbots database
revision and reports `Unknown Playerbots Database Revision` when it is empty.
The base SQL defines the latter as the applied-update record. The empty revision
table therefore has a concrete diagnostic consequence, but is not by itself
evidence that applied updates are missing; compare update hashes/files before
drawing that conclusion.

The observed DEV state includes core/module and project tables such as
`custom_unlocked_appearances`, Individual Progression quest rows, Character
Services NPC data, and MorphSummon appearance/unlock tables. Such observations
prove present rows only; they do not establish which source installed them or
that tracked SQL can recreate the exact state.

## Cross-database application model

The required high-level order is:

```text
core database creation/updates -> module schemas and data by database
-> Playerbots database creation/updates -> project custom-world manifest
-> deployment-specific checks
```

**VERIFIED.** The project manifest is an explicit post-module `acore_world`
overlay. **UNKNOWN.** A complete, tested order for every installed module across
all four databases is not documented. The installer neither backs up data nor
makes its batch atomic. Do not infer that cached Playerbots data is disposable;
the safe recovery classification of its tables is unestablished.

## Project-owned custom SQL

The current custom SQL inventory is entirely under
`data/sql/custom/db_world/`. It contains world-data customizations such as
class/race changes, riding overrides, vendor content, item and loot changes,
quest chains, and transmog currency loot.

`data/sql/custom/db_world/manifest.txt` is the authoritative ordered inventory
of project custom world SQL — not the directory listing. `manifest.txt` must
list every `*.sql` file in the directory exactly once; run
`scripts/apply-db-world.sh --validate` to prove that, because an omission makes
the installer refuse to touch the database. Known inventory drift is tracked
in [`../debt/REGISTER.md`](../debt/REGISTER.md).

The installer streams each listed file in manifest order to the `acore_world`
database using the local `azeroth-dev` MySQL login path and stops at the first
failed file. The manifest uses one top-level SQL filename per line, without
comments or blank lines.

To add or remove custom world SQL, update `manifest.txt` in the same change and
place the file according to its verified dependencies. The manifest is a
post-module overlay: Individual Progression mount overrides and Naxx40 curio
loot require that module's data to be installed first. The installer does not
create a database backup, wrap the full batch in a transaction, or install
custom character or auth SQL.

## Safety implications

Apply order is defined only by `manifest.txt`, never by filenames or locale.
SQL authors must record prerequisite relationships in the component
documentation and make required rerun behavior explicit in the SQL itself. Do
not run the installer against a production database without an explicit approved
operational procedure.
