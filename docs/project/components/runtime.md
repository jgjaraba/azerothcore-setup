# Runtime and configuration

## Build and install layout

The observed CMake cache installs the local AzerothCore build at
`~/azerothcore/env/dist` with `MODULES=static` and `BUILD_TESTING=OFF`.
`authserver` and `worldserver` are installed in `bin/` below that prefix.

**OBSERVED (2026-09-20).** The current build cache selects Clang, core and
script precompiled headers, `TOOLS_BUILD=all`, and disables tests. Its
`CMAKE_BUILD_TYPE` cache entry is empty, while the top-level CMake default is
`RelWithDebInfo`; generated build flags reflect that default. These are cache
observations, not a tracked clean-build policy. The distributed configuration
defaults differ for build type and tools, so they must not be assumed to
reproduce this build directory.

Core CMake collects static module sources, generates a combined loader, and
builds a static `modules` library. It copies module `.conf.dist` templates into
the install configuration tree. The installed module source set is therefore a
build input; editing a static module or core requires a compatible rebuild and
install before restarting the server.

## Configuration ownership

Runtime `authserver.conf`, `worldserver.conf`, and module configuration files
are located in `env/dist/etc/`. The core repository ignores the install tree,
so these local files are not project-controlled configuration artifacts.

`scripts/common.sh` maintains the runtime `LogsDir` settings. Before modifying
either server configuration it creates a one-time adjacent `.bak` copy. This is
a local configuration rollback aid, not a database or system backup mechanism.

**OBSERVED (2026-09-20).** Effective files exist in `etc/` and `etc/modules/`.
Non-secret allowlisted settings show Playerbots, Character Services, Dungeon
Clear, MorphSummon, and Quest Loot Party enabled; Character Services faction
change is disabled. Database credentials and full configuration values remain
local secrets and are not copied into this knowledge base. Presence of an
effective setting is not a live-server or gameplay validation.

The installed binaries, DBC/maps/vmaps/mmaps, logs, PID files, and effective
configuration are deployment state. Their presence does not prove that binaries
were built from the current checkout or that server DBC matches tracked client
assets.

**Observed server-DBC discrepancy (2026-09-20).** The tracked `dbc/Item.dbc`
contains `90001`–`90005`, while the installed server `bin/dbc/Item.dbc` contains
none of `90001`–`90005` or `91001`–`91079`. The files have different SHA-256
hashes. DEV nevertheless has the matching item-template rows. This is a current
server-data alignment risk, not evidence about either client MPQ's contents or
about live item behavior.

## Local lifecycle scripts

`scripts/start.sh`, `status.sh`, and `stop.sh` manage only the development
installation at `env/dist`. They serialize operations with a runtime lock and
validate both the executable path and `-c` configuration path before treating a
process as this development instance.

They must not be assumed to manage production processes or other AzerothCore
installations.

## Change implications

- **Configuration only:** update the effective file through an approved process
  and restart; startup-cached modules may not react without restart.
- **Database only:** install module prerequisites and project overlays in their
  documented order, perform appropriate checks, then restart where data is
  cached at startup.
- **Core or static module source:** configure/build/install the compatible
  source set, review generated configuration, and restart.
- **Server DBC or client data:** deploy matching server data, distribute the
  matching client artifact, restart/relaunch as applicable, and test the
  player-visible contract.

These are dependency implications, not a substitute for a tested deployment or
rollback procedure.
