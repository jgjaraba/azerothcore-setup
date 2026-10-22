# azerothcore-setup
My configs and scripts for AzerothCore

## OpenCode workspace and project knowledge

- [`docs/project/README.md`](docs/project/README.md) — the durable knowledge
  base for this project. Read it first; it indexes the architecture, component
  and feature documentation, ADRs, identifier registry, debt register and
  durable learnings.
- OpenCode runs directly from this repository: `cd ~/azerothcore-setup && opencode`.
  Its project configuration is `opencode.jsonc`, agents are in `.opencode/agents/`,
  and durable instructions are in `AGENTS.md`.
- `scripts/agent/validate-opencode.sh` checks the active project configuration.

## Apply project server customizations

The existing scripts remain the server entry points. From this checkout:

```sh
scripts/apply-core-patches.sh --validate
scripts/apply-db-world.sh --validate --with-server-data
```

`apply-core-patches.sh` applies the ordered source patches, including the Turtle
extractor patch. Set `REPO=/path/to/azerothcore` for another checkout. Build/install
the core/modules as appropriate after source changes, and apply their upstream
database updates before the project world SQL.

With the target server stopped and exclusive access to its files/database:

```sh
REPO=/path/to/azerothcore scripts/apply-core-patches.sh
scripts/apply-db-world.sh --with-server-data \
  --data-dir /path/to/effective/DataDir \
  --state-dir /path/outside/DataDir/project-data-state \
  --offline
```

The world script applies its existing SQL manifest, then installs the server
assets in [`data/server/manifest.json`](data/server/manifest.json). Turtle instance
and access SQL are already in that SQL manifest. The assets include geometry,
collision/navigation and five **row-level DBC deltas**, not full replacement
tables. The complete file plan is checked **before any SQL**; conflicting files
are not overwritten. `--offline` asserts stopped/exclusive targets; it does not
stop services itself. Configure the MySQL login with `LOGIN_PATH` (default
`azeroth-dev`, database `acore_world`).

No arguments still means **SQL only**. `--validate --with-server-data` verifies
both inventories/hashes without database or target access. Repeating installation
with the same state verifies/reuses installed files; individual SQL files retain
their own rerun semantics. The complete SQL manifest plus files is **not one
atomic transaction**. Preserve the state and see [deployment/recovery details](docs/turtle-wow/deployment.md).
Neither script installs client patches.

## Client setup

### Turtle WoW migration

- [Migration guide and technical index](docs/turtle-wow/README.md) — the accepted
  Karazhan Crypt pilot, repeatable stages, client/server safety and remaining
  limitations.
- [Long-term custom-content roadmap](docs/turtle-wow/roadmap.md) — geography
  first, then server scenery and gameplay with explicit compatibility gates.

### 1. Download WotLK client
**Regular Client**

```https://www.chromiecraft.com/en/downloads```

**HD Client**

```https://discord.gg/UyjSg8wRcs```

### 2. Install server patch

Download [patch-Z.mpq (regular client)](client_patches/regular_client/patch-Z.mpq) or [patch-Z.mpq (hd client)](client_patches/hd_client/patch-Z.mpq)

#### 2.1 (HD Client only) Classic login screen

If you use HD client and want to see always the classic login screen, copy [loginui.lua](client_patches/loginui.lua) into your client `Interface` directory.

#### 2.2. Optional patchs
* [Classic Dungeon Maps](https://github.com/Trimitor/WDM-patch)

#### 2.3. Turtle Karazhan Crypt — manual client installation

Install the matching server data above first. Client files are kept directly in
[`client_patches/turtle_crypt/`](client_patches/turtle_crypt/), not only under ignored
`work/`. Verify them with `sha256sum -c SHA256SUMS` from that directory.

**Accepted custom esES package:** copy all three files from
[`r5-coordinated/Data/`](client_patches/turtle_crypt/r5-coordinated/Data/) to the
same relative paths under your playing client's `Data/`:

| Repository file below `r5-coordinated/` | Client destination |
|---|---|
| `Data/patch-T.MPQ` | `Data/patch-T.MPQ` |
| `Data/patch-Z.mpq` | `Data/patch-Z.mpq` |
| `Data/esES/patch-esES-Z.MPQ` | `Data/esES/patch-esES-Z.MPQ` |

Close WoW first. Back up replaced files **outside `Data/`**, and record files
that did not previously exist. Replace/revert this set together; do not leave
duplicate names differing only in case. For rollback restore the original files
and remove only the newly added ones. The two Z files preserve the audited custom
client and reconcile its old crypt resources. This is **not an arbitrary-client
merge**. It is the user-tested custom esES distribution; do not copy its root Z
over the HD patch or assume compatibility with other custom archive chains.
The existing regular/HD downloads above are unchanged.

**Optional stock esES variant:**
[`stock-esES/Data/patch-T.MPQ`](client_patches/turtle_crypt/stock-esES/Data/patch-T.MPQ)
contains only the pilot contribution merged against its declared stock baseline.
It needs no replacement Z, but is **not** a drop-in update for custom/HD clients.
Check its exact baseline before copying manually:

```sh
python3 tools/crypt_release_client.py preflight \
  --client /path/to/clean-esES-client \
  --report client_patches/turtle_crypt/stock-esES/report.json
```

If that passes, copy its T into `Data/` with WoW closed and no existing T; rollback
removes that newly added file. This stock variant passed binary/installer checks,
but has **not** received a separate in-game visual acceptance. Do not remove a
custom client's other patches to force this preflight to pass.

### 3. Addons

* [Questie](https://github.com/Aldori15/Questie) / [Questie experimental build](addons/Questie-335.zip)
* [AtlasLoot](https://github.com/Wrath-AddOns/AtlasLoot_ChromieCraft) / [AtlasLoot experimental build](addons/Atlasloot.zip)
* [Bagnon](https://github.com/RichSteini/Bagnon-3.3.5)
* [DungeonClear](https://github.com/jrad7/mod-dungeon-clear-addon)
* [MultiBot-Chatless](https://github.com/Wishmaster117/MultiBot-Chatless)
* [PlayerbotManager](https://github.com/Lichborne-AC/PlayerbotManager)
