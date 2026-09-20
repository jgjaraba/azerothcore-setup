# Database and custom data

## Database configuration boundary

The local authserver and worldserver configuration files define login, world,
and character database connections. Their connection values are local ignored
runtime configuration and are intentionally not duplicated in project
documentation.

## Project-owned custom SQL

The current custom SQL inventory is entirely under
`data/sql/custom/db_world/`. It contains world-data customizations such as
class/race changes, riding overrides, vendor content, item and loot changes,
and transmog currency loot. Current filenames and working-tree state are
generated in `../generated/ENVIRONMENT.md` and must be checked before changes.

`data/sql/custom/db_world/manifest.txt` is the authoritative ordered inventory
of project custom world SQL. `scripts/apply-db-world.sh` validates the manifest
before database access: every listed file must exist exactly once and every
`*.sql` file must be listed. It then streams each file in manifest order to the
`acore_world` database using the local `azeroth-dev` MySQL login path and stops
at the first failed file. The manifest uses one top-level SQL filename per line,
without comments or blank lines. `--validate` performs only manifest validation.

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
