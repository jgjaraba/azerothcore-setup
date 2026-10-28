# High-elf Map0 server data

`tools/build_high_elf_server_data.py` builds isolated server geography from the
published **regular** client, official-name stock archives, final terrain/assets
evidence and the relocatable cartography deltas in
`client_patches/archive/source-inputs/high-elf-map/deltas/`.

```sh
export TMPDIR="$PWD/work/tmp"
python3 tools/build_high_elf_server_data.py all --output work/high-elf-server-build
python3 -m unittest discover -s tools -p test_build_high_elf_server_data.py -v
```

Use a fresh output for changed inputs. The phases `prepare`, `geometry`,
`locales`, `navigation`, and `report` can be resumed individually. Inspect a failed command
before retrying; cached successful commands are reused. A different wrapper
revision requires explicit `--reuse-previous-wrapper` after inspection, with
the acceptance recorded in `reuse-audit.json`. `inputs.json` pins source
archives, tool binaries, DBC baselines/deltas and consumed neighboring Maps.
`logs/` records native commands, return codes and diagnostic text. `report.json`
and `intended-files.json` are staging-local evidence/file plans, **not** additions
to the global server manifest and not an installation mechanism.

## Extraction contract

- Stock custom T/Z/F/M/N archives are excluded. Stock inputs are symlinks;
  regular archives are private copies. Original client and runtime paths are
  read-only inputs. Linux locale archive filenames need canonical aliases.
- The client T owns geography but deliberately contains no DBC. The extractor
  patch opens T last and does not promise to load locale custom Z. Derived
  extraction T therefore contains the independent server AreaTable/WMOAreaTable
  merges (including final cartography audio), server LiquidType and a map-0-only
  extraction Map.dbc. No client-localized full table replaces the server baseline.
- `server-dbc/Map.dbc` is the complete server table, retaining map 800. Neither
  `Map.only0.dbc` nor `Azeroth.subset.wdt` is installable server/client content.
- Maps extraction uses only the selected 24 MAIN entries. A separate native
  extraction with the same DBC and WDT restriction identifies byte-equivalent
  unchanged output despite ADT reserialization. In particular native `33_22`
  should not be deployed just because its installed `.map` differs in encoding.
- VMap extraction uses the **full** continent WDT. All map-0 placements are
  assembled together. The closure includes every model named by every resulting
  map-0 VMap tile, not just models in the 24 selected ADTs. Existing `.vmo` files
  must hash identically; a different same-name model is a conflict, never an
  implicit overwrite.
  Some serialized M2 spawn names contain a trailing NUL: the native loader's
  appended `.vmo` then falls after that NUL, and the actual flat filename ends
  in `.m2`. Include these VMAP-format binaries in closure; a `*.vmo` glob alone
  is incomplete. The wrapper uses the native C-string filename semantics.
- Navigation uses the generated Maps and complete VMap set. Native Maps remain
  visible for cardinal border strips. The selected tiles and their cardinal halo
  are generated explicitly; halo-only tiles can change because neighboring
  height strips changed. Input dependencies extend one more tile where needed.
- Coordinate convention: ADT `(X,Y)` becomes generator `--tile X,Y`,
  `maps/000YYXX.map`, `mmaps/000YYXX.mmtile`, and
  `vmaps/000_XX_YY.vmtile`. Server grid/load APIs may reverse X/Y again.
- The installed generator currently rejects `--help` as an invalid map ID.
  Inspect `src/tools/mmaps_generator/PathGenerator.cpp` for its accepted switches;
  do not infer coordinate order from filenames. An exit code of zero without an
  output tile is not automatically success. Empty native terrain without an
  installed MMap can legitimately produce none; changed navigable tiles cannot.

## Existing schema2 installation

`tools/stage_high_elf_server_data.py` preserves the audited build under
`data/server/high-elf-map/` and extends the existing `data/server/manifest.json`
to schema2. Staging does not install anything. The existing
`tools/apply_project_server_data.py`, called by
`scripts/apply-db-world.sh --with-server-data`, implements the following
contract, with the runtime stopped and backup/recovery for the coordinated set.
Use the [deployment instructions](deployment.md), not a parallel installer.

A changed manifest requires a new state directory: the helper binds each journal
to the manifest hash and rejects an older manifest's state. Reapply the same
manifest with its own existing state. Preserve older states and their matching
sources/manifests for recovery; do not edit or delete journals to bypass identity
checks.

### Cambio de una fila DBC ya instalada

La corrección de la posada cambia únicamente WMOAreaTable60017:
`(root6002, nameSet0, group19746)` → `(root6002, nameSet0, group0)`.
60016/group−1 sigue intacta; no hay fallback de grupo. El delta nuevo no puede
aplicarse aditivamente sobre la fila antigua: el collision guard debe rechazarla.
La migración live corresponde al principal, con backup y verificación de ownership
semántico completo de la fila anterior, cambio específico de60017, comprobación
before/after de las demás filas/strings y aplicación del manifiesto con un estado
nuevo. Una fila desconocida sigue siendo colisión; no autoriza reemplazo silencioso.

`client_patches/archive/high-elf-map-v3-before-inn-group-fix.tar` conserva las fuentes
anteriores completas, su source lock, el manifiesto servidor anterior y su delta
WMO para recuperación. Extraerlo en una ubicación aparte: no añadir archivos al
directorio activo bloqueado. El cambio no requiere regenerar Maps, VMaps ni MMaps.

The coordinated payload contains23 Maps (not native-equivalent `33_22`),
`000.vmtree` and374 complete map-0 VMap tiles, a2951-model closure (2914
hash-identical native models and37 new models),34 MMaps (23 regional and11 halo)
with `000.mmap`, and four additive DBC deltas. The combined project manifest
plans3414 destinations; the audited DEV application changed474 files, not all
3414. These counts do not authorize overwriting an unrecognized baseline.

1. Revalidate all build source hashes and target baseline hashes before writing.
    The staging report records both; schema2 preserves accepted preimage hashes
    for scoped replacements and neighboring Map dependencies. Replan on drift
    instead of overwriting an unknown target. Hash-identical files need no write.
2. Apply only the changed regional Maps, omitting native-equivalent `33_22`.
   Preserve all other maps and all other map IDs.
3. Replace `000.vmtree` **together with the complete generated map-0 VMap tile
   set**, including tiles far outside the new region. Tree node indices and
   placement IDs are assembly-global: copying only 24 VMap tiles next to a new
   tree is invalid. Keep the matching generated `.vmo` closure available; reuse
   existing files only by exact hash. If an installed map-0 tile is absent from
   the new complete set, investigate/retire that stale file as part of the same
    coordinated replacement; schema2 rejects unexpected stale map-0 tiles
    rather than leaving an old-tree tile active.
4. Install the generated regional and halo MMaps plus compatible `000.mmap`
   parameters. Compare origins, tile dimensions, polygon capacity and tile
   capacity against the remaining installed map-0 MMaps. Native MMaps outside
   the rebuild can remain only with matching coordinates/parameter geometry and
   sufficient capacity. Do not reset the entire `mmaps/` directory.
5. Merge the durable AreaTable/WMOAreaTable/WorldMapArea/WorldMapOverlay deltas
   against each destination server's own baseline, preserving unrelated rows
   (including crypt800). Staged full tables are evidence on the observed DEV
   baseline, not portable replacements for another server's tables. Map and
   LiquidType need no deployment if unchanged.
6. Retain the generated complete VMap tiles adjacent to the region, even where
   the selected terrain tile itself has no WMO. Placements can overlap tile
   boundaries. For navigation, retain the recorded neighbor Maps used by the
   generator and install changed halo results, not just the selected rectangle.

The helper already supports these replacements, complete-tree/model closure,
MMap compatibility/dependency checks and additive DBC merging. Installation and
same-state reapplication were executed on DEV, followed by restart through the
existing scripts; see [scoped evidence](validation.md#altos-elfos-mapa0--alcance-de-la-evidencia).
The state/backup directory is operational recovery material outside DataDir;
preserve the actual installation state rather than substituting a path from docs.

Generation, format checks, closure, hashes and deployment establish offline/file
consistency. They do not establish in-game LoS, swimming, NPC paths,
cross-region gameplay or client rendering. The [geographic contract](high-elf-maps.md)
also records native WDL/Light, audio and cartography limitations.
