# Runtime and configuration

## Build and install layout

The observed CMake cache installs the local AzerothCore build at
`~/azerothcore/env/dist` with `MODULES=static` and `BUILD_TESTING=OFF`.
`authserver` and `worldserver` are installed in `bin/` below that prefix.

## Configuration ownership

Runtime `authserver.conf`, `worldserver.conf`, and module configuration files
are located in `env/dist/etc/`. The core repository ignores the install tree,
so these local files are not project-controlled configuration artifacts.

`scripts/common.sh` maintains the runtime `LogsDir` settings. Before modifying
either server configuration it creates a one-time adjacent `.bak` copy. This is
a local configuration rollback aid, not a database or system backup mechanism.

## Local lifecycle scripts

`scripts/start.sh`, `status.sh`, and `stop.sh` manage only the development
installation at `env/dist`. They serialize operations with a runtime lock and
validate both the executable path and `-c` configuration path before treating a
process as this development instance.

They must not be assumed to manage production processes or other AzerothCore
installations.
