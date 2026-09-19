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

`scripts/apply-db-world.sh` discovers every `*.sql` file in that directory,
sorts paths lexicographically, and streams each file to the `acore_world`
database using the local `azeroth-dev` MySQL login path. It stops at the first
failed file. The script does not create a database backup, wrap the full batch
in a transaction, or install custom character or auth SQL.

## Safety implications

Apply order is determined by filenames. SQL authors must therefore consider
earlier custom files as prerequisites and make any required rerun behavior
explicit in the SQL itself. Do not run the installer against a production
database without an explicit approved operational procedure.
