# Turtle WoW maps port

Design and implementation contract for porting Turtle WoW's custom geography
(Vanilla 1.12.1) into the WotLK 3.3.5a client and AzerothCore DEV.

## Objective and scope

Bring Turtle WoW's custom maps, terrain modifications, and cartography into the
WotLK 3.3.5a client and server while preserving all WotLK and project content.

In scope: terrain (ADT/WDT), water, models/WMOs/textures referenced by the maps,
DBC (Map/AreaTable/WorldMapArea/LoadingScreens), server Maps/VMaps/MMaps/DBC, and
the client patch packaging.

Out of scope (later phases): quests, NPCs, loot, spells, combat scripts, dungeon
mechanics.

## Architecture

- **Source**: `/home/dev/wow-turtle` (Vanilla 1.12.1, build 5875). Read-only.
- **Destination reference**: `/home/dev/wow-335` (WotLK 3.3.5a, build 12340).
  It is not assumed to be the active playing client or permanently synchronized
  with it. Original inputs are not edited; tested packages are installed in
  the user's chosen client separately.
- **Format boundary**: dry-pilot and high-elf terrain/reference adaptations have
  been demonstrated, not blanket Vanilla/WotLK compatibility. The parser and
  serializer MHDR layout is corrected; the high-elf compositor retains source
  MH2O and disables duplicate MCLQ. No general MCLQ→MH2O project converter is
  implemented. Alpha, optional chunks and asset fidelity still require
  per-resource verification. See the curated compatibility reference.
- **Patch strategy**: consolidated regular `patch-T.MPQ` owns crypt and high-elf
  geography without DBC; root/locale Z own the coordinated tables/cartography.
  Use `client_patches/README.md` for current manual installation. Historically,
  the refreshed user-supplied snapshot had old terrain and a conflicting
  map-800 DBC row in both root Z and esES Z, which shadow T. For that snapshot,
  `tools/build_pilot_overlay.py` prepares derived Z copies with only those
  conflicts reconciled, preserving unrelated content. Original input archives
  are never edited. Install/revert the coordinated set in a separate playing
  client using the package instructions; re-audit if its source hashes differ.
- **Project deployment**: [existing scripts](../../turtle-wow/deployment.md) own
  source patches and SQL. The world script's explicit `--with-server-data` mode
  installs the final repository payload in `data/server/manifest.json`, including
  collision closure and narrow DBC deltas. Schema2 also supports high-elf scoped
  map0 replacements and additive DBC merges. Current client MPQs live in the
  consolidated regular profile; historical crypt packages remain separately in
  `client_patches/turtle_crypt/`. Neither script installs client files.
  The historical stock variant excludes unrelated r5
  WorldMapArea changes and is not a replacement for custom/HD distributions.
  A from-source rebuild and complete private-server bootstrap remain distinct.

## Tooling (project-owned, `tools/`)

| Tool | Purpose |
|---|---|
| `mpq.cpp` + StormLib | MPQ list/extract/create (V2 archive format, matching `patch-Z.mpq`) |
| `dbc.py`, `dbc_write.py` | WDBC read/write |
| `adt.py`, `adt_dump.py` | ADT parse/dump |
| `adt_convert.py` | Vanilla → WotLK ADT converter (re-serializer) |
| `mpq_priority.py` | MPQ patch-chain priority resolution |
| `asset_index.py` | 335 asset existence + `.mdx`→`.m2` resolution |
| `extract_tiles.py`, `adt_inventory.py` | continent tile diff/inventory |
| `merge_pilot_dbc.py` | DBC merge for the pilot map |
| `build_crypt_cartography.py` | r3: additive WorldMapArea/TRS merge and image packaging |
| `stage_crypt_server_worldmap.py` | matching server coordinate metadata, preserving its own DBC baseline |
| `build_crypt_portals.py` + `crypt_portals.json` | r4 native access: additive AreaTrigger DBC, fail-closed SQL and coordinated package |
| `build_crypt_loading.py` | r5: Turtle loading art and additive LoadingScreens table, coordinated Map updates |
| `crypt_release_client.py`, `crypt_release_dbc.py` | isolated stock-client distribution and collision-checked row transplant |
| `crypt_release.py`, `crypt_release_server_{data,db}.py` | deterministic portable bundle, transactional install, reapply and recovery |
| `apply_project_server_data.py` | internal file-plan/install/recovery helper for `apply-db-world.sh`; no SQL/client deployment |
| `high_elf_map_dbc.py`, `high_elf_terrain.py`, `high_elf_map_assets.py`, `high_elf_map_cartography.py` | scoped map0 DBC, terrain composition, assets and cartography |
| `package_high_elf_map.py` | source-locked regular consolidation hook |
| `build_high_elf_server_data.py`, `stage_high_elf_server_data.py` | isolated extraction and preservation into the existing schema2 server manifest |

## Pilot cartography contract

Revision 3 (`work/client-overlay-r3/Data/patch-T.MPQ`) adds the Turtle
illustrated crypt plan (12 world-map textures), six Turtle exterior minimap
tiles and 23 interior aliases under the pilot's custom WMO namespace.
Group identity and dimensions are checked: 18 interior images use Turtle art,
five retain native art where bounds differ. No working geometry is changed
to fit images. The complete 335 minimap TRS and existing WorldMapArea rows
are preserved; global Turtle DBC/Lua replacement is prohibited.

The user-confirmed coordinated Z copies from r2 remain unchanged; upgrading
that playing client only replaces T with WoW closed. Server coordinate metadata
adds only the matching row on the server's own baseline. Installation, backup,
hashes and pending visual tests are recorded in the validation document.

The user has confirmed r3 cartography in game. An optional Spanish-art edition
translates its five baked world-map labels using current Turtle Spanish DBC
terminology, leaving all map coordinates, minimap and geometry unchanged.
`tools/localize_crypt_map.py` preserves untouched DXT1 blocks and packages
`work/client-overlay-r3-esES-final/Data/patch-T.MPQ`. This edition displays
Spanish labels for any interface locale using that archive; it does not add
automatic language selection. The user subsequently supplied improved manual
artwork. Its aligned/paletized package
`work/client-overlay-r3-esES-manual-ready/Data/patch-T.MPQ` was confirmed in
game and is the cartography baseline for r4.

The user confirmed r4.1 native entrance/exit work in game. Revision5 adds the
effective Turtle loading screen (LoadingScreens511, Map800 field57) and retains
all validated pilot content. This upgrade replaces **T and both coordinated Z
copies together**, because Z owns competing Map.dbc and old loading art. Use
`work/client-overlay-r5/INSTALL.md`; prior T-only instructions do not apply to
this refinement. The user subsequently confirmed the screen works in game.

Third-party (StormLib, wowdev listfile) and extracted artifacts live under
`work/` and `tools/` (gitignored); only project code is versioned.

## Conversion procedure (reproducible)

The [migration guide](../../turtle-wow/migration-guide.md) is the operational
reference. The stages below describe the integration chain, **not** a single
clean-clone bootstrap. Current builders consume hash-pinned intermediate
packages and some local audit inputs; the manual Spanish PNG must be preserved.
The [roadmap](../../turtle-wow/roadmap.md) keeps future work separate from this
feature contract.

1. `tools/extract_tiles.py` / `mpq extract` — pull the source ADT/WDT.
2. `tools/adt_convert.py` — remap `.mdx`→`.m2`, remap area IDs, re-serialize.
3. `tools/merge_pilot_dbc.py` — add Map/AreaTable rows to the effective 335 DBCs.
4. `tools/mpq create` — build `patch-T.MPQ`.
5. `map_extractor`/`vmap4_extractor` (with `patch-T.MPQ` support) — extract
   Maps/VMaps/DBC from the integrated client.
6. `mmaps_generator <mapid>` — navigation meshes.

## Extractor modifications

`map_extractor` (`LoadCustomMPQFiles`) and `vmap4_extractor` (`patch-T.MPQ` +
`--only <mapid>`) were extended to load the custom patch. These are native
tool-source changes, not gameplay changes. They are preserved under ADR-0003 in
`patches/core/turtle-pilot-extractors.patch`; its companion document records
baseline, limits and tool-specific build/rollback. T-last extraction does not
reproduce the game's root/locale priority automatically.

## Pilot: KarazhanCrypt (map 800)

Integrated pilot with user-confirmed exploration, presentation, access,
temporary-follower movement and the agreed short wall/floor/water checks.
Practical geographic validation is accepted; exhaustive navigation/regression
coverage remains outside that acceptance:

- Map 800 `KarazhanCrypt` (dungeon), area 5086 `Karazhan Crypt`.
- 6 ADTs + WDT adapted; MMID indirection repaired and an isolated native crypt
  WMO variant removes the WotLK-only barrier. Filename existence alone is not
  a compatibility proof. All4,123 M2 placements retain their intended models.
- Server data generated: DBC,6 map tiles,6 vmap tiles and6 MMap tiles. The last
  MMap uses a scoped0.9 contour-simplification override, with offline native
  path/LoS checks; this does not certify all room connections or NPC movement.

## High-elf geography on native map0

The [high-elf contract](../../turtle-wow/high-elf-maps.md) owns the extensive
Highlands5225 / Alah'Thalas2040 addition:24 composed ADTs, source MH2O water,
isolated props/WMOs, additive DBC/cartography and coordinated regular-client
publication. Area3881–3883 remaps to6500–6502, preserving native Outland.

The [server-data contract](../../turtle-wow/high-elf-server-data.md) covers23
changed Maps, full map0 VMap tree/374 tiles,2951-model closure and34 regional/halo
MMaps plus parameters. Installation/reapplication uses the existing helper and
schema2 manifest, not a new installer. This geography adds no SQL, NPC, quests
or playable-race starting data. Structural/deployment evidence does not establish
client rendering or in-game collision/navigation by itself. Later bounded real
client checks cover loading, dry/wet controls, minimaps and continental clicks;
the user confirmed access and corrected liquids, not exhaustive gameplay.
Native WDL/Light and adapted audio/cartography impose explicit fidelity limits.
The [migration guide](../../turtle-wow/migration-guide.md) consolidates the full
procedure; the [project skill](../../../.opencode/skills/turtle-zone-import/SKILL.md)
and its template drive future imports without generalizing the region's IDs or
hash-pinned adaptations.

## ID allocation

| ID | Namespace | Value | Notes |
|---|---|---|---|
| Map | 800 | `KarazhanCrypt` | free in WotLK (max 724) |
| Area | 5086 | `Karazhan Crypt` | free in WotLK |
| Area | 6500–6502 | high-elf subareas | source3881–3883; native Outland retained |

See `../../turtle-wow/id-mappings.md` for the full register and collision rules.

## Installation / rollback

- Compatible target: use the [project scripts](../../turtle-wow/deployment.md)
  and manual client setup in the root README. The server manifest includes all
  405 collision-model dependencies, not only `800*` files. Identical existing
  binaries are accepted and DBC baselines are merged. File recovery uses the
  durable state directory and does not roll back SQL. The prior portable export
  has a different, ten-rows-absent installation contract and must not be chained
  after applying the normal SQL manifest.
- The following r5/older-package instructions concern the existing custom
  client/DEV installation, not stock-clean deployment:
- Client: use the coordinated r5 T/root-Z/esES-Z set and package instructions,
  with backups outside Data. Unlike the earlier r4/r4.1 upgrades, r5 requires
  all three updated archives because loading-screen data is also present in Z.
- Server: merged `Map.dbc`/`AreaTable.dbc` in `bin/dbc/` (originals backed up as
  `*.bak-pre-turtle`), `maps/800*.map`, `vmaps/800*`, `mmaps/800*`.
- r4-only rollback: stop DEV, apply its guarded access rollback SQL, restore
  the saved AreaTrigger.dbc and restart; restore the preceding manual-map T
  in the playing client. Do not undo all pilot data merely to revert access.
  Details and backup paths are in the validation document and package INSTALL.

## Validation

See `../../turtle-wow/validation.md`. Binary/server generation checks have run;
they do not establish complete LoS or navigation behavior. The user confirmed
entry and exploration of the crypt after the coordinated revision-1 overlay.
The user also confirmed revision2 fixes exterior artifacts, revision3 map and
minimap work, and the manual Spanish artwork is satisfactory. Walking entrance
and exit, loading-screen presentation, temporary follower movement, the short
wall/between-floor checks and water/well-edge checks are also user-confirmed. These close
the practical pilot validation, not exhaustive route coverage or the whole
Turtle port. Level-limit/group/corpse cases were not explicitly reported.

## Known limitations

- Exterior model markers revealed an MMDX/MMID conversion defect: shortening
  model paths requires recalculating MMID offsets, not just changing names.
  Revision 2 fixes the table and preserves all placement identities and the
  working crypt barrier correction. Clients already using coordinated r1 Z
  copies replace only T with `work/client-overlay-r2/Data/patch-T.MPQ`.
  The user confirmed this repair in game. It is preserved by later packages.

- The initial same-filename asset reuse preserved a WotLK-only invisible
  stair barrier. The user confirmed entry to map 800 but could not descend.
  A namespace-isolated WotLK-native crypt variant removing only that barrier
  is packaged in `work/crypt-fix/revision-1/patch-T.MPQ`; its geometry and
  regenerated collision files pass structural checks. The user subsequently
  confirmed crypt access and exploration. See the validation document for the exact
  artifact, hashes, installation and rollback backup.
- Native map0 ↔ map800 access is implemented as an r4 data/SQL overlay.
  It uses a pre-barrier entrance box and the authentic Turtle exit sphere;
  DEV deployment and user walking validation are confirmed. The existing map0 WMO
  stays intact. See [native-access contract](../../turtle-wow/crypt-portals.md).
  The first r4 client DBC hid the entrance by appending a map0 record after
  map724; r4.1 corrects stable MapID ordering, preserved in the current r5 package.
  SQL and volumes are unchanged. Use `work/client-overlay-r4.1/INSTALL.md`.

- The missing MMap `[35,52]` is now generated and installed using a localized
  configuration override, without core changes. Native offline queries pass
  for the350 complete tested point-pair/filter combinations;410 remain
  partial/disconnected, especially deeper/water regions. Actual NPC movement
  and the remaining connections still require validation. See
  [navigation contract](../../turtle-wow/navigation.md).
- No general ADT liquid (`MCLQ`→`MH2O`) converter is implemented. The high-elf
  path preserves source MH2O; crypt WMO liquid is a separate resource format.
- The crypt uses a modified isolated native WMO. High-elf props/WMO and real
  particle fixtures extend structural conversion evidence, but neither establish
  universal WMO/M2 fidelity. Bounded client rendering checks are recorded
  separately; they are not coverage of every asset, floor or path.
