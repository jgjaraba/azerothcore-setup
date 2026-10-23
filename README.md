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
collision/navigation, five geographic **row-level DBC deltas**, and a natural-key
delta for seven Troll facial styles—not full replacement tables. The complete file plan is checked **before any SQL**; conflicting files
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

#### 2.4. Racial customizations — choose ONE cumulative patch-S

Both editions are complete replacements installed as **`Data/patch-S.MPQ`**.
**Never load both**, rename one to another patch letter, or copy the whole package
tree into the client. With WoW closed, back up your owned S **outside Data** and
copy only the selected edition's file. Keep T/Z/locale-Z unchanged; do not
overwrite an unrelated S without reconciling it first.

| Edition | File | Includes |
|---|---|---|
| **Primary / complete options** | [client_patches/Data/patch-S.MPQ](client_patches/Data/patch-S.MPQ) | Accepted Troll primary plus Tauren: one full-face skin per sex, six horn colours, ten native barber-style unlocks and four additional facial adornments. |
| **Optional / partial options** | [client_patches/optional-extra-skins/Data/patch-S.MPQ](client_patches/optional-extra-skins/Data/patch-S.MPQ) | Everything in primary, the retained9+9 Troll appearances, plus3 male /2 female fixed-face Tauren looks, including the identified Spirit Walker shop bake. |

Verify `SHA256SUMS` in `client_patches/` or `client_patches/optional-extra-skins/`.
Copy only the selected file to the playing client's **Data/patch-S.MPQ**. The old
`turtle_forest_troll/` packages are frozen build bases/history, not current extras
to load beside it. Every subsequent race migration follows this same two-edition
policy: complete ordinary-face coverage in primary, fixed-face/partial looks in
optional, both cumulative and mutually exclusive.

Original indices and Troll resource bytes are preserved, including the removal
of male Troll33–35. Tauren's missing facial pieces are appended to the **native
Wrath models** with verified bone bindings; native skeleton/animations remain.
No new race, display, morph or aura is added. The user confirmed the Tauren
implementation works perfectly; this is practical acceptance, not an exhaustive
DK/HD matrix. Mixed-edition viewing still lacks optional resources in primary;
see the [Tauren contract and compatibility discussion](docs/turtle-wow/tauren-customizations.md).

The default server manifest now installs491 overlays (Troll298 +Tauren193) and
eleven facial-style donor rows through the existing world-SQL/`--with-server-data`
flow. Use a fresh file-state directory when upgrading the changed manifest.
The optional manifest adds150 (Troll135 +Tauren15), **not applied by default**.
To opt in after
the primary server setup, with the server stopped:

```sh
SQL_DIR="$PWD/data/sql/optional/db_world" scripts/apply-db-world.sh
```

Restart afterward. Use the optional client wherever characters with extra skins
are selected or viewed: primary lacks those records/textures and cannot promise
correct rendering of them. Existing characters are not remapped when switching
profiles. Recustomize extra skins in an optional-capable client before switching
to primary, or keep using the optional edition for those characters.

Upgrading an older optional profile with the same command removes the21 exact
legacy rows for retired male colors33–35. Conflicting foreign changes fail closed;
other skins, hairstyles and facial features are preserved. Retired indices are
not renumbered or reused.

To disable partial looks, remove Tauren's optional15 first using
`data/sql/rollback/turtle_tauren_extra_skins.sql`, then Troll's135 using
`data/sql/rollback/turtle_troll_extra_skins.sql`; keep principal facial/hair/Forest
data. Existing appearances are never remapped automatically. Default reapply
does not silently remove an enabled opt-in. Contracts: [Tauren](docs/turtle-wow/tauren-customizations.md),
[Troll](docs/turtle-wow/troll-customizations.md), and the permanent
[edition policy](docs/project/decisions/ADR-0007-native-customization-editions.md).

### 3. Addons

* [Questie](https://github.com/Aldori15/Questie) / [Questie experimental build](addons/Questie-335.zip)
* [AtlasLoot](https://github.com/Wrath-AddOns/AtlasLoot_ChromieCraft) / [AtlasLoot experimental build](addons/Atlasloot.zip)
* [Bagnon](https://github.com/RichSteini/Bagnon-3.3.5)
* [DungeonClear](https://github.com/jrad7/mod-dungeon-clear-addon)
* [MultiBot-Chatless](https://github.com/Wishmaster117/MultiBot-Chatless)
* [PlayerbotManager](https://github.com/Lichborne-AC/PlayerbotManager)
