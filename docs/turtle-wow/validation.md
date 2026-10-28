# Turtle WoW maps — validation

Record of what was actually tested, with evidence, and what remains pending.

## Altos Elfos mapa0 — alcance de la evidencia

Contrato vigente: [high-elf-maps.md](high-elf-maps.md); extracción e instalación:
[high-elf-server-data.md](high-elf-server-data.md). Esta sección resume evidencia
ejecutada de la implementación. El log final de ejecución conserva el detalle
principal de comandos/resultados; los manifiestos source-locked de terreno,
assets y cartografía conservan los contratos estructurales. La generación
servidor tiene su detalle local en `work/high-elf-server-build/report.json`,
`final-build.log` y `logs/`.

- **PASS estructural:**24 tiles compuestos,3899 MCNK fuente y2245 nativos;
  no nuevas regresiones de costura entre las comparaciones disponibles de12464
  bordes examinados. **SIN BASELINE:**16 bordes, excluidos de esa conclusión.
  MH2O de origen se conserva como autoridad
  y se desactiva el MCLQ duplicado; no se ejecutó una conversión general MCLQ→MH2O.
- **PASS estructural de modelos:**los10 emisores de partículas del árbol,
  contrastados con OracleTree nativo; no es evidencia de renderizado.
- **PASS entrega de archivos:** regular publicado con316 miembros en T sin DBC,
  root Z con28 y cada locale Z con6 (totales finales, no altas del port).
  S, launcher y HD sin cambios por
  este port. Fuente durable, baselines y resultados fijados por source lock.
- **PASS generación servidor:**23 Maps (se omite `33_22` nativo sin delta),
  árbol mapa0 y374 tiles VMap completos; cierre2951 modelos (2914 nativos
  idénticos +37 nuevos);34 MMaps (23 región +11 halo), parámetros compatibles
  y cuatro deltas DBC aditivos, preservando mapa800 y datos ajenos.
- **OBSERVED / despliegue DEV:** instalación y reaplicación realizadas por el
  helper existente con manifiesto schema2:3414 destinos,474 cambios en la
  instalación inicial. Reinicio posterior mediante los scripts existentes.
  El estado real de instalación/backup se conserva fuera de DataDir. La receta
  reutilizable es `scripts/apply-db-world.sh --with-server-data --data-dir
  /ruta/DataDir --state-dir /ruta/estado --offline`; validación de inventario con
  `scripts/apply-db-world.sh --validate --with-server-data`.
- **PASS arranque DEV:**112 data stores inicializados; `WORLD: World Initialized`
  y `worldserver ... ready` tras instalar la versión con clave interior exacta
  `(6002,0,0)→6502`. La comprobación posterior del manifiesto y su diario encontró
  los3414 destinos idénticos y verificó529 dependencias. Esto no fuerza la carga
  jugable de toda la región.
- **PASS carga con lectores nativos offline:**43 Maps (24 región +19 halo),
  árbol mapa0 y374/374 VMap tiles,2951 modelos y522/522 MMap tiles aceptados por
  Detour. Probe: `tools/build_high_elf_nav_probe.py`; evidencia local en
  `work/high-elf-native-validation/REPORT.md` y `evidence.json`.
- **Consultas offline, resultado mixto:**191 casos,117 corredores completos,
  47 parciales (8 con `OUT_OF_NODES`) y27 sin consulta por destino no disponible.
  Los seis casos entre muestras de Alah'Thalas, Brinthilien y Highlands, con
  filtros walk y walk+swim, obtuvieron corredores completos. Hubo90 impactos
  VMap con altura/rayo concordantes y LoS bloqueada. No es una certificación
  de todas las rutas ni de movimiento NPC. Un vecino adicional de halo,
  `maps/0002133.map`, está ausente y no cuenta como carga superada.
- **PASS regresión Error132:** el paquete anterior producía39 lecturas inválidas
  en `0x007C3A42` y2288 celdas con tags desconocidos al ejecutar la rutina x86
  real de ambos EXE locales (stock y new-races). Tras normalizar únicamente el
  tamaño propio de MCLQ inactivo, la extracción del T publicado completa6144/6144
  llamadas en cada EXE, con0 faults,0 tags desconocidos y0 recorridos fuera de
  límites. Evidencia: `work/crash-go-investigation/final-published-fixed.json`.
  Se regeneraron24 Maps, árbol/374 VMap tiles y2951 modelos: todos byteidénticos
  a los datos servidor anteriores; sus DBC también coinciden. No hubo que
  reinstalar ni reiniciar el servidor por esta corrección cliente.
- **PASS carga real acotada:** cliente12340 enUS/Wine/D3D9, personaje Human GM,
  Brinthilien y Alah'Thalas cargados durante60 segundos cada uno. Se renderizaron
  personaje y entorno, respondieron comandos/logout y no se creó Error132.
  Evidencia: `work/high-elf-client-load-check/report.json`, screenshots y hashes.
  **Defecto visual de esa versión:** minimapa verde sólido, corregido por la
  entrega cartográfica comprobada abajo.
- **PASS regresión de volúmenes rojos:** se reprodujeron ambos `error_red_*` en
  cliente real enUS/Wine/D3D9. Antes: SWIMMING activo y magma visual en
  `4558.568,-2869.236,10` y `3167.174,-2422.720,118`. Después de adaptar solo
  MOHD en15 familias, ambos puntos permanecieron secos, sin velo/partículas
  anómalas tras60s, en primera y tercera persona; también cerca del suelo sin
  vuelo y en las columnas Alah Z40/42/44 y Brin Z170/172. Se verificaron las XYZ
  reales y el bit nativo SWIMMING. Evidencia A/B:
  `work/high-elf-red-check/after-fix/report.json` y `REPORT.md`.
- **PASS agua legítima:** `4572.916667,-2868.75,-2`, por encima de suelo−6.739
  y bajo agua0: natación, movimiento, azul y respiración conservados tras60s.
  Caminar sobre superficie con waterwalk desactiva SWIMMING; se retiró el cheat
  al terminar. No se eliminó el agua real para ocultar los volúmenes falsos.
- **PASS servidor sin delta:** reextracción con la entrega WMO corregida y
  procesamiento de43 candidatos de navegación (34 tiles,9 vacíos); cierre2951
  modelos,374 VMap tiles. Maps, modelos, árbol, tiles VMap/MMap, parámetros y
  DBC siguen byteidénticos; preflight3414 destinos y0 escrituras. En los puntos
  rojos reales, las consultas servidor anteriores y regeneradas ya son secas.
  Evidencia: `work/high-elf-server-wmo-dry-fixed/result.json`.
- **PASS cartografía cliente real:** enUS/Wine/D3D9 con T
  `491b64ce0df41215d9459736a5ac207cca6f9da0d06d9c27a934bd05f3bc01c0`.
  Exteriores Alah y Brinthilien texturizados y estables60s, con movimiento real.
  HouseVariantF muestra el plano circular y desplazamiento coherente bajo la
  flecha; Silver Sun Mine muestra su minimapa interior y responde al movimiento.
  Los otros grupos se verifican por lookup/payload, no por visita completa.
- **PASS selección continental:** hover nativo y clic izquierdo real abren
  ThalassianHighlands y AlahThalas; clic derecho vuelve al continente. Las dos
  celdas del borde conservan Western/Eastern Plaguelands, y el control Tirisfal
  también conserva hover/clic. Sin selección directa por ID ni addon sustitutivo.
- **PASS preservación cartográfica:** las44 celdas ZMP previstas son el único
  delta de máscara;29 mappings crypt e imágenes efectivas idénticos (sin nueva
  visita a la cripta). Terreno, WMO, líquidos, DBC, S, Z y ejecutable no cambian.
  Comprobados de nuevo en cliente los dos puntos rojos y el mar legítimo: secos donde
  corresponde y natación/azul en el mar. Evidencia y límites:
  `work/high-elf-map-ui-check/REPORT.md` y `report.json`.
- **NOT RUN / no acreditado aquí:** recorrido/render exhaustivo, swimming,
  LoS, rutas NPC y gameplay/regresiones en juego. Se retienen WDL/Light nativos,
  audio nativo Eversong y cartografía2D/minimapa de fuentes mixtas; no hay claim
  de fidelidad total ni activación servidor de nuevas razas.

## Existing project scripts and repository assets — historical crypt evidence

Normal procedure: [deployment.md](deployment.md) and the root README. Runtime
assets are retained in `data/server/turtle-crypt/` and
`client_patches/turtle_crypt/`, rather than requiring ignored release inputs.

- **PASS:** SQL manifest validation and core-patch validation. In a separate
  local clone, the five affected source files were restored from clean HEAD;
  both source patches applied through `apply-core-patches.sh`, and repeating
  the script detected both as already applied. No source changes were made
  to active DEV for this test. The documented base mismatch warning remains.
- **PASS:** `apply-db-world.sh --validate --with-server-data`:430 files verified;
  server manifest SHA256
  `b7a71ca62e98eb049fe45313f46383a1182538ff371d57104d4c31265b65e5b3`.
  A read-only plan against active DEV found all430 target outputs byte-identical.
- **PASS:**21 new file-helper/shell tests plus38 existing release tests with the
  proprietary fixture enabled. Includes physical server `.m2` models, rejection
  of client MD20, pre-SQL collision/drift checks, durable recovery, and explicit
  file-only rollback. Bash syntax and independent implementation review passed.
- **PASS:** real private-MySQL test with `--project-workflow`, exercising the
  existing shell script, **only the two canonical Turtle SQL units**, and all430
  repository server files. Install/reapply preserved expected bytes and ten
  SQL rows; file-only rollback deliberately left SQL intact and did not touch
  client MPQs. A binary collision failed before SQL/state mutation. Report:
  `work/crypt-project-workflow-test-r1/report.json`. The private server was stopped.
- **PASS:** all five client checksum entries; repeated staging accepted identical
  outputs. The regular/HD distributions were not replaced. Building the former
  portable export directly from the repository assets, without historical
  `work/` inputs, reproduced manifest SHA256
  `dd99f86fbe2578857167731034076e3a0d6611fdcc08a3d5ad0413fb97bdb5d2`.
- **NOT RUN:** applying the whole project world manifest in this test, compiling,
  starting a complete pristine realm, or launching/revalidating the stock client
  in game. The MySQL fixture remains schema plus unrelated native rows and
  representative native server files, not a complete realm bootstrap.

## Portable clean-target release: installer validation

Procedure and contract: [portable-release.md](portable-release.md). This is distinct from
the earlier coordinated custom-client r5 distribution and its gameplay acceptance.

Local delivery: `work/crypt-release-r3/`, and `work/crypt-release-r3.tar`
(47,749,120 bytes). These proprietary artifacts are ignored by Git; preserve
them privately together with their hashes. No external backup is implied.

| Artifact | SHA256 |
|---|---|
| Release `manifest.json` | dd99f86fbe2578857167731034076e3a0d6611fdcc08a3d5ad0413fb97bdb5d2 |
| Deterministic transport tar | 171d6f14304b693af1e8f5bff2edaf8a63015037c942060c17cc89d93f356817 |
| Clean-esES `client/Data/patch-T.MPQ` | b77c897d0147e7f8759569c4f6e54e07f1f7e06cf2d011f7583a3405237d8a48 |

- **PASS:** two independently built clean-client MPQs are byte-identical. All
  64 art/geography resources are byte-identical to accepted r5. Stock DBC rows
  and string prefixes, including Ruby Sanctum609, are preserved; the104 unrelated
  donor WorldMapArea additions are excluded. Only29 pilot TRS aliases are added.
- **PASS:** independently built portable releases have the same manifest hash;
  independently packed transport tars have the same SHA256.439 files are
  inventoried, including430 server payload files and all405 collision-model
  dependencies. The repaired navigation tile is included.
- **PASS:**38 release unit/fixture tests, with the proprietary fixture test
  enabled. Cover collisions, malformed inputs, ordering, DBC string relocation,
  corruption, preparation failure, idempotency, rollback and recovery.
- **PASS:** `tools/test_crypt_release_integration.py` on the final bundle with
  a private MySQL8.4.11 instance, networking disabled. The fixture used current
  table definitions plus one unrelated row per owned table, stock-client DBCs,
  representative native server files, and read-only stock MPQ hardlinks.
  Install added exactly ten SQL rows. Reapply preserved bytes/rows. Rollback
  restored original files/absence and unrelated SQL. Real transactions recovered
  from pre-COMMIT connection close, committed-SQL/partial-file failure, and a
  simulated lost acknowledgement after COMMIT. Bundled standalone CLI install
  and rollback also passed. Report: `work/crypt-release-integration-r3/report.json`.
- **PASS:** independent implementation review; its preparation-state diagnostic
  finding was corrected and covered by a regression test.
- **NOT RUN:** boot of a complete pristine realm, launch/gameplay of the new
  clean-client distribution, whole-private-project restoration, and a complete
  rebuild from original clients. The isolated installer fixture is not a claim
  that those tests ran. Existing gameplay acceptance below remains scoped to r5.

The private MySQL test instances were stopped. No deployment was performed to
the active DEV realm or the user's playing client for this release validation.

## Pilot practical acceptance: short in-game checks

After confirming correct temporary-rabbit behavior, the user performed the
agreed short checks and reported:

- Wall between rooms: **OK**.
- Between floors: **OK**.
- Water and well edge: **OK**.

These are user-performed gameplay results, not agent-observed client execution.
Together with the earlier exploration, cartography, loading-screen and portal
confirmations, they close the agreed **practical geographic pilot validation**.
No additional client/runtime changes were required for this acceptance.

The scope remains bounded: no precise locations or full route matrix were
supplied for these short tests. They do not certify every room connection,
NPC underwater pathfinding, descent into the well, corpse/group/level-limit
cases, or resolve the410 partial/disconnected diagnostic combinations.
Those remain documented limitations/follow-ups; the entire Turtle geography
port is not declared complete.

## Navigation revision1: complete tile set, scoped acceptance

The user confirmed the Turtle loading screen works, then approved completing
navigation/collision checks. Live inspection confirmed missing
`bin/mmaps/8005235.mmtile`. A fresh isolated baseline reproduced the native
71,281-vertex rejection (generator exit0 despite failure). The true accepted
vertex maximum is65,534 (`>=0xffff` is rejected); no format-limit patch was made.

Experimented only with the tile's `maxSimplificationError`, retaining voxel
resolution2000/80, slope60, height6/climb4/radius2 and all geometry. Results:
0.85 generated63,883 vertices but failed22 of350 complete diagnostic surface
traversals.0.9 generated54,745 vertices/33,379 polygons and passed all350.
1.0 and1.2 generated fewer vertices but were not selected. The scoped0.9
profile is now in `tools/crypt-nav-800.yaml.in`; YAML tile key52,35 corresponds
to CLI35,52. No installed global config or core was modified.

Tools added: `crypt_nav_generate.py`, native `crypt_nav_probe.cpp`, its build
wrapper, `crypt_nav_queries.py` and `crypt_nav_report.py`. Native Detour/VMap
libraries load actual generated files. `CanLoadMap` must validate VMap inputs
before `LoadMapTile(y,x)` to avoid false empty-tile success. Compilation and
linking passed; the nine native C++ codestyle checks were applied to the owned
probe and passed. Input file hashes and native ABI/header versions are checked.

Evidence: `work/server-data/crypt-navmesh-r1/validation.json` and underlying
TSV/control/report/log files. The final generation writes all six tiles with
no error diagnostics. Existing five tiles and800.mmap are byte-identical to
the baseline. Single-tile and full-map generation give the same new tile.

The suite combines20 actual sampled/reference points, directions and ground /
ground+water filters:760 queries. Baseline five-tile data completed12; the
candidate completes350 and preserves those12. All350 completed diagnostic
native-surface traversals pass,195,858 sampled steps at0.4 units with zero
body-height VMap ray intersections.4,927 bounded polygon-edge reprojections
are explicitly counted. Direct straight-path height interpolation was not
treated as movement validation because it can intersect detailed sloped floors;
the probe follows the surface with corridor updates instead.

Four controls pass against both staged and deployed data: a174.5-unit detour
between hallway floors sharing almost the same XY; blocked direct LoS but a
clear149-unit doorway route; clear corrected stair passage; blocked LoS/no
complete route between the well room and ossuary69 units lower (no spurious
vertical floor snap). Candidate endpoint snaps are at most0.475 units. The
stair floor from native VMaps matches the user's previous GPS60.156513.

**Residual limitations are part of the result, not passes:**410 combinations
remain partial/disconnected. Ground data joins the main dry corridor/room
samples; water-mode adds one sinkhole sample and a separate ossuary/ramp/hall
component, not global 3D swimming. Group18820 has no chosen ground sample.
No forced offmesh link was added. The offline probe is not execution of a live
Unit/PathGenerator and uses different step/buffer settings; LoS rays are not a
full swept-body collision check. Do not declare the entire instance navigable.

Independent review rebuilt the probe, reexecuted760 queries and controls,
matched the TSV exactly, confirmed all existing files identical and approved
adding only the missing tile. Before deployment, backed up five tiles+map
params and recorded that the new file was absent in
`work/server-data/crypt-navmesh-r1/recovery/before.json`. With DEV stopped,
installed only8005235.mmtile and restarted. Its deployed SHA256 is
`20da70c08443295bcf916be3c1c8974b01534efa8de08b92d044d143cbe4e20e`.
Native controls against the actual DataDir then reproduced staged output
exactly (`runtime-controls.tsv`). No client, SQL, DBC, VMap, terrain or
installed generator-config change was needed. MoveMaps/LoS/height are enabled
in the inspected DEV config.

The user test protocol is documented in `navigation.md`: inside map800, summon the
existing passive Rabbit721 with `.npc add temp 721`, select it and use actual
`.mmap path` / `.npc follow` for short dry-ground routes; `.debug los` checks
a wall separately. No NPCs were spawned/persisted by the agent.

**Initial user confirmation:** the temporary rabbit behaves correctly. That
accepted the tested follower movement after the tile installation, without
enumerating rooms/routes or reporting the short wall/floor checks yet. The
user subsequently supplied those short results; see the practical acceptance
section above. Full-room route coverage and deep/underwater connectivity are
still not certified.

## r5: source Turtle loading screen

**User-confirmed:** r4.1 world entrance and exit now work correctly. Requested
the effective Turtle loading screen as the final current pilot refinement.

Source Turtle patch9 Map.dbc map800 field38 points at LoadingScreens511;
its three-field LoadingScreens record names `Karazhan Crypt` and the path
`Interface\\Glues\\LoadingScreens\\LoadScreenKarazhanCrypt.blp`. The effective
image comes from Turtle patch4, not patch9: source SHA256
`1c0de23be00e87706286616e72c74a035986ee7ff0b31a7fb49a2a39926ddcbd`.
It is BLP2 DXT1, 512x512, opaque, with ten active mip levels and the
Mysteries of Azeroth logo. The root Z overlay contained the older patch3
artwork at the same case-insensitive path, so T alone cannot replace it.

`tools/build_crypt_loading.py` builds three coordinated copies from r4.1:

* T/root-Z/esES-Z each preserve their own Map.dbc. Only row800, field57
  (the **335** LoadingScreenID field) changes from0 to511. All other bytes
  remain intact, including each file's independent string block.
* The effective native 335 LoadingScreens baseline has4 fields/91 rows.
  ID511 was checked free, including references from other maps. An additive
  merge produces92 rows, retaining all91 original records and strings. The
  new row uses the source name/path and HasWideScreen0. No matching Wide
  resource exists; it is not requested.
* T gains the merged table and image (69→71 resources);68 original resources
  are byte-identical. Root Z changes only Map.dbc and its old loading image;
  the remaining39 resources are identical. esES Z changes only Map.dbc;
 24 other resources are identical. AreaTrigger and the approved manual Spanish
  map/minimap/WMO content remain unchanged.

The source BLP has invalid stale descriptors after the dimensionally valid
ten mip levels: offset10 points at EOF with an overflowing size and size15
is nonzero without an offset. The builder zeros only offset/size entries
10–15. Length, all other header fields, palette and every active DXT1 byte
are preserved. Normalized BLP SHA256:
`ca2931c47bccb42766d8dd24ea32cf394433e6290b5c0fbd6487769ab41ccbc2`.
Pillow13 decodes source and normalized image to exactly the same RGBA pixels.
No artwork or aspect conversion was performed.

Five tests pass, every archive resource was round-trip checked, two fresh
builds produced identical hashes for all three MPQ, and independent review
verified the actual archives, source provenance and per-byte change scope.
Preview: `work/client-overlay-r5/loading-preview.png`. Reports:
`work/client-overlay-r5/{report,verification}.json`.

| r5 artifact | SHA256 |
|---|---|
| Data/patch-T.MPQ | 738ef0e3547f2d40ad9e7fbb7ed5608d684bbb51e640b5328b4bf26cce1813ee |
| Data/patch-Z.mpq | 3b4082bfabc3f02a1efedca81b973548d56f56e32cde6ed4609aa0a2e919d3b0 |
| Data/esES/patch-esES-Z.MPQ | 2de9f73504a6ad457942e8cdc5d9aad55fa663395fda7b4c70f0f3bbec5f19b0 |

Install/rollback must treat **all three archives as a set**; see
`work/client-overlay-r5/INSTALL.md`. This supersedes the earlier T-only upgrade
instructions for this revision. Original clients and server/runtime/SQL were
not modified. DEV Map.dbc's unused multimap_id remains0; screen presentation
is client-side and does not require a server reload.

**Pending in-game:** entrance portal loading, relog inside, return screen on
map0, native-instance regression and aspect presentation on the playing client.
The image and packaging checks are not claimed as a game-render test.

## r4.1: repair hidden client entrance trigger

**User-observed r4 failure:** portal visible, neither GM nor normal player can
enter; map0/area2563/phase1 at (-11068.088,-1825.5011,60.15711), orientation
1.602479, remains blocked at the original crypt barrier.

The static build12340 investigation found a concrete packaging defect. In the
inspected executable (SHA256
`bf644876709c591acc17c0da8cdf1814edcc9f1e6bc109a8c0d5c38c79dc953c`),
0x6D2F70 delimits a contiguous block of 40-byte AreaTrigger records for the
current map and stops at the first greater MapID. The r4 file appended entrance
900800/map0 after native map724: its index1220 was not in map0's [0,175) scan
range. Exit900801/map800 at1221 was included. Checking existence by ID and
preserving a native byte prefix did not validate the client's range lookup.

The examined emitter sends the full 32-bit trigger ID in CMSG_AREATRIGGER
(0x0B4); no uint16 truncation was found in that path. IDs were not changed.
The reported GPS lies just beyond the entry box's narrow edge, before the
original barrier; failure to activate during the approach is consistent with
the excluded row. This is not proof of packets from the playing installation.

`merge_dbc()` now stably orders raw records by MapID, preserving all1220 native
record bytes, float bits, strings and relative native order. Entrance900800
is at175, within map0's corrected [0,176) range; exit900801 remains at1221.
Both are checked against a simulation of the actual per-map scan. Seven tests
pass, including a regression reproducing the exact append-and-hide defect.
Independent review checked the client code and real MPQ/DBC outputs and found
no blockers. Of69 r4 payloads only AreaTrigger.dbc changes. SQL, nine deployed
rows, portal positions, volume dimensions and all68 preceding resources are
unchanged. No further collision geometry was removed.

Deliverable: `work/client-overlay-r4.1/Data/patch-T.MPQ`
SHA256 `0c6e851df5961c0062ba47b617b25078c29b67dacf7278d1b77a259ab031a681`.
DBC SHA256 `e28e09f4480662b512801fa9a670b7a42aa28939738376a7081ae2ea1c537aae`.
The builder accepts the exact previous r4 server file only as a migration
input, but never emits that invalid ordering again.

The corrected server DBC file was installed after backing up the previous
owned r4 file under `work/client-overlay-r4.1/recovery/`. No SQL was reapplied
or service restarted for this change: ObjectMgr/HandleAreaTriggerOpcode uses
SQL `areatrigger`, not this DBC file. Read-only verification confirms all nine
deployed rows remain exact. Source clients were not changed.

Next user test: install r4.1 T with WoW fully closed, retain coordinated Z,
restart client, step back to the accessible side (return position at
-11068.9,-1828.6,60.4) and approach normally. A GM can enable
`.debug areatriggers` before crossing: accepted entry ID900800 should produce
a chat diagnostic, and exit ID900801 likewise. Toggle again after testing.
Silence alone does not distinguish no packet from earlier server rejection;
network debug can be used next if needed. Activation, transfer and landing
still require in-game validation; the fix is not declared gameplay-tested.

## r4: connect the pilot dungeon to the world

The user confirmed the manually edited Spanish map is satisfactory and
requested the next pilot step: entrance/exit as a dungeon. Research contract,
source provenance, IDs and coordinate adaptations are documented in
`crypt-portals.md`; versioned source of truth is `tools/crypt_portals.json`.

Native client/server shapes use project aliases 900800/900801. Turtle's entry
ID5008 collides with Nagrand Arena and is preserved. The authentic Turtle
entrance lies behind native map0 collision, so the entrance was placed on the
reachable side of the unchanged barrier. The interior destination and exit
follow the Turtle data, with small Z clearances above measured floors.
This is a deliberate WotLK compatibility adaptation, not an exact world-space
copy of the source doorway. No map0 WMO, ADT or collision file is overridden.

Implementation adds two trigger volumes, two native teleports, two decorative
portal templates/spawns (native display672, type5, scale1.6), and access
template124 (normal difficulty, minimum level55). No keys, quests, requirement
rows, creature spawns or dungeon gameplay scripts are imported. Source
Turtle/Tortoise data has a separate key gate; it is intentionally outside this
geographic pilot. SQL is tracked in the ordered world manifest.

Validation actually performed:

* Six offline tests pass: preservation of native DBC data including5008,
  uint32/float32 layout and malformed/conflicting input rejection, rotated
  entrance reachability before the barrier, no-bounce destinations with a
  conservative1.5-yard margin, floor clearance, quaternions/phase and SQL sync.
* Builder preserves all68 resources of the user-approved manual-map T and
  adds only AreaTrigger.dbc:69 payloads, round-trip verified. DBC1220→1222,
  all old records/strings exact. Coordinated Z copies are unchanged.
* Independent review found no outstanding blockers. A second build before
  deployment and a third after deployment produced an identical MPQ.
* Before database changes, filtered backups of the five affected tables and
  the native server AreaTrigger.dbc were saved in
  `work/client-overlay-r4/recovery/`. All nine new rows were absent.
* With DEV stopped, applied the SQL twice. `check_dev()` confirmed all nine
  rows match every expected field (float tolerance1e-3; radius0 exact).
* Executed the guarded rollback once and confirmed the nine rows absent.
  Reapplied and confirmed all nine exact. Existing instance metadata and native
  portal template188096 remain unchanged. The exceptional SQL handler was
  reviewed but not tested by injecting a failure.
* Installed the client-identical AreaTrigger.dbc in DEV and restarted. The
  fresh log reports1219 SQL Area Trigger Definitions and274 Teleport
  Definitions and reaches ready state. These counts establish loading, not
  walking activation or visual alignment.

Forward SQL uses a short-lived project-prefixed routine for atomic exception
rollback; identical reruns do not overwrite rows. Conflicting ownership or
unexpected bindings fail closed. Rollback generation is in the builder and
its deployed copy is in `recovery/rollback_crypt_access.sql`.

Deliverable: `work/client-overlay-r4/Data/patch-T.MPQ`, SHA256
`306ed487a090a1f6a4f32494ce520c9ef58a12375beb8179a367f0e02cbb4614`.
Server AreaTrigger.dbc SHA256:
`be68c90027c9dc874a5b9eecb955425a239b8ffcca3082e7098c5a59ff7011ca`.
SQL SHA256:
`f60861d4aebae154d471de0f1bad8b10bb84d81de218e9554b4829c4dbf6e109`.

No source/reference client was modified. Install only the new T in the actual
playing client with WoW closed; retain the coordinated Z files. Instructions
and recovery: `work/client-overlay-r4/INSTALL.md`.

**Pending in-game:** walk through entrance before hitting the native gate,
arrive safely on map800, walk back through exit to map0 without rebounce,
level54 denial/55 acceptance without GM bypass, solo/group and corpse return,
visual portal alignment and original Karazhan regression. Do not mark the
connection validated until those relevant user tests are recorded.

## User-supplied manual Spanish map

User supplied `work/karazhan-crypt-map-edit/fixed-es.png`, SHA256
`e8c52e1752375a27da6dafe789eed57ae295b137c78f4d469fe4f02b6e40ecee`.
The PNG was not modified. Its canvas is 1024x768 RGBA, but its visible artwork
is 1024x685 rather than the original 1002x668: direct strict reimport would
change transparency and visual coordinate alignment.

`tools/align_crypt_map_png.py` creates a separate registered derivative, with
no label repaint. SIFT/RANSAC found 512 inliers among 599 matches, spanning
979x663 pixels. Original-to-edited scale is 1.02321092, rotation -0.012496°,
median registration error 0.590 px, p95 1.513 px. The original alpha is exact.
The aligner validates full Lanczos4 support, including source transparency,
rejects significant clipping and preserves marginal original frame pixels
instead of introducing opaque black. For this input 10,438 boundary pixels
(1.559% visible) were preserved. Independent review reproduced a previously
identified coverage defect, verified its correction, and measured zero newly
introduced opaque black pixels in the final derivative.

Aligned derivative:
`work/karazhan-crypt-map-edit/manual-aligned-final/fixed-es-aligned.png`,
SHA256 `5d73e5576883cee2afdd7a8c21e9a1723920a2be795450768a31742b7f87ae87`.

The deliverable uses `crypt_map_png.py import --palette`: classic-compatible
BLP2 encoding 1, 255 opaque palette colors plus reserved transparent index,
and an independent exact 8-bit alpha plane. This avoids the lettering block
artifacts observed in the DXT1 comparison preview. RGB is still quantized,
not lossless. A dedicated decoder validates the separate alpha plane because
Pillow's palettized BLP reader uses palette padding for alpha instead. Tests
cover that distinction. Raw BGRA encoding 3 was explored but rejected for
this delivery because pre-Cataclysm support was not established; no such
candidate is included in the final package.

Final deliverable:
`work/client-overlay-r3-esES-manual-ready/Data/patch-T.MPQ`
SHA256 `175a802e1ff52f4210c429b652e05c170e8dfadca7dbd312bc5b6bf1386bdfd3`.
Decoded preview: `work/client-overlay-r3-esES-manual-ready/resultado.png`.
Exactly 12 WorldMap tiles change; all other 56 r3 resources remain identical.
Independent review regenerated the same aligned PNG and MPQ byte-for-byte,
verified alpha and preview, and found no remaining blockers. Six tests pass
(four import/encoding tests and two alignment-coverage tests).

No client originals, Z copies, server data or runtime were changed. Install
only T with WoW closed and retain the coordinated Z copies. The package's
INSTALL.md documents input provenance, image treatment, rebuilding and rollback.
Validation of the manually edited map inside the 335 client is still pending.

## Spanish artwork feedback and manual-edit exports

The user confirmed the Spanish edition loads in game, but rejected the
lettering/restoration quality compared with the original. Technical image
integrity is not evidence of acceptable artistic quality. The user offered
manual editing; the original English and current Spanish plans were exported
losslessly instead of presenting another unproven automatic repaint as final.

Exports: `work/karazhan-crypt-map-edit/{original-en,actual-es}.png`.
Both are RGBA 1024x768, preserving the original 4x3 arrangement of 256x256
tiles and all transparent padding. A separate transparent guide layer and
Spanish instructions (`guia-rotulos.png`, `LEEME.md`) are included. The source
MPQ and PNG hashes are recorded in `manifest.json`.

`tools/crypt_map_png.py` supports reproducible export and reimport of an edited
PNG. Reimport requires the original dimensions, RGBA mode and alpha; it keeps
untouched DXT1 blocks and all non-world-map resources, then verifies every
archive entry by round-trip extraction. A decoded preview is included for the
new manual artwork. DXT1 can change colors within edited 4x4 blocks, so a
manual PNG is not promised pixel-identical after compression.

Validation performed:
- Export/redecode preserves every source RGBA pixel.
- Reimporting the unedited English PNG produces the exact original r3 MPQ
  SHA256 `2532cc09a85b9495637391aaf4ffed2f2d0b44ca857ed3c376ea09fedb5ec35d`.
- Three tests pass: one opaque pixel changes exactly one tile/one compressed
  block; resized canvas and altered transparency are rejected.
- Independent review confirmed exports, reimport behavior and unchanged
  geographic/minimap/DBC content. No source clients or runtime were modified.

No further automatic lettering changes were installed. Pending: the user's
manually edited PNG and its subsequent in-game visual approval.

## Optional Spanish-art edition of revision 3

**User-confirmed:** revision 3 world map and minimap function correctly. The
user requested Spanish localization of the illustrated plan.

No drawn Spanish variant was found in the provided Turtle snapshot. Both
patch-4 and effective patch-9 world-map image families contain English labels.
The five current Spanish terms were verified directly in Turtle patch-9:

| English label | Spanish label used |
|---|---|
| Karazhan Crypt | Cripta de Karazhan |
| Pauper's Walk | Paseo del Indigente |
| The Slough of Despair | El Cieno de la Desesperación |
| The Upside-down Sinners | Los Pecadores Colgados |
| Tomb of the Unrepentant | Tumba de los Impenitentes |

The title comes from AreaTable row 5086, field 17. Interior terms come from
WMOAreaTable WMOID 3833, NameSet 0, groups 18701/18812/18811/18815, field 17.
The native 335 Spanish term “Libro de los Impenitentes” corresponds to a
different English Tome/Tomb spelling and was not substituted for Turtle's
verified “Tumba”. Merely editing DBC text cannot change these baked labels.

`tools/localize_crypt_map.py` reconstructs the twelve-tile canvas, removes
only five bounded label regions, draws their Spanish text using the pinned
Turtle FRIZQT font, and updates only intersecting 4x4 DXT1 blocks. Original
BLP headers, dimensions, tile positions and every other block remain intact.
Dependencies are pinned in `tools/crypt-map-localization-requirements.txt`.
The script reads labels directly from the source DBCs and rejects disagreement.

Final archive:
`work/client-overlay-r3-esES-final/Data/patch-T.MPQ`
SHA256:
`13ca6b6eb430eff93edb62840d267594b35f2c49e9d2dd47994fbe0cf1cd9233`.
Preview: `work/client-overlay-r3-esES-final/spanish-map.png`.

Independent verification extracted both MPQs: exactly seven world-map BLP
change (2,3,4,5,10,11,12); 61 other content entries and the listfile remain
byte-identical. The 1,673 changed DXT1 blocks are confined to authorized
regions. All twelve alpha channels are pixel-identical. The decoded map
matches the preview. Visual inspection found no clipped labels or residual
English text. A repeated build produced an identical archive.

Observed tool versions: Pillow 13.0.0, OpenCV 4.12.0, NumPy 2.2.6. Executed:

```sh
/tmp/opencode/crypt-maps-research/venv/bin/python tools/localize_crypt_map.py \
  --output work/client-overlay-r3-esES-final
```

Installation replaces only T on the actual playing client, with WoW closed;
keep the coordinated Z copies and backups outside Data. Rollback restores r3
T. No source/reference clients, server data or runtime were modified.
**This is an optional Spanish-art edition for any locale using that T**, not
automatic locale selection. The original English-art r3 archive remains
available. In-game render validation of the translated edition is pending.

## Cartography revision 3

The user confirmed revision 2 removes the exterior markers and requested
Turtle world-map/minimap integration as the next pilot step.

Implemented `tools/build_crypt_cartography.py` with no temporary-research-file
dependency. Sources are freshly extracted from the clients and their hashes
recorded. The build uses the confirmed coordinated revision-2 package rather
than the unsynchronized `/home/dev/wow-335` T/Z snapshot.

* Twelve effective Turtle patch-9 `Interface/WorldMap/KarazhanCrypt/` images
  form the illustrated interior crypt plan; no Turtle FrameXML is imported.
* Client WorldMapArea is merged into the effective 335 locale-N baseline:
  212 → 213 rows, preserving all original record bytes and strings. Added
  row 674 links map 800/area 5086 to `KarazhanCrypt`, with Turtle bounds and
  335 display-map/default-floor/parent fields -1/0/0. No overlay artwork rows
  or numbered dungeon-floor DBCs are needed for this unnumbered plan proposal.
* The effective 335 minimap TRS is preserved as a complete byte prefix and
  extended with six terrain mappings and 23 new `tw800crypt` group aliases:
  18,644 → 18,673 mappings. No existing mapping is overwritten.
* All six terrain images are Turtle's. The interior images match by MOGP
  group ID, not array index: Turtle and native groups have different orders.
  Eighteen interior images use Turtle artwork with matching XY bounds and
  grid/dimensions. Five use native aliases (target groups 000,002,003,009,017)
  because Turtle bounds or image dimensions differ. This preserves alignment
  with the working native WMO; it is not claimed as an all-Turtle interior
  minimap. Imported hashed images use unique tw800-prefixed filenames.
* BLP2/DXT1 header dimensions, mip sizes, offsets and ranges are checked.
  All referenced added minimap images resolve. The research inspection
  decoded Turtle art; actual 335 display/selection remains untested in game.
* Every one of the original 30 r2 payloads, including MMID and collision WMO,
  remains byte-identical. Round-trip extraction verifies all 68 r3 payloads.
  Z copies remain byte-identical to r2. Source archives were not modified.

Fourteen regression tests passed, independent review found no concrete bugs,
and a second build produced identical MPQ and payload bytes. Evidence:
`work/client-overlay-r3/{report,verification}.json`.

Build/test commands:

```sh
python3 -m unittest discover -s tools -p test_crypt_cartography.py
python3 tools/build_crypt_cartography.py --output work/client-overlay-r3-new
```

Client artifact `work/client-overlay-r3/Data/patch-T.MPQ` SHA256:
`2532cc09a85b9495637391aaf4ffed2f2d0b44ca857ed3c376ea09fedb5ec35d`.
Clients already on coordinated r2 only replace T, with the game stopped;
installation and rollback are in `work/client-overlay-r3/INSTALL.md`.

Server coordinate synchronization uses
`tools/stage_crypt_server_worldmap.py` and the server's own baseline (108 →
109 rows), not the client's larger table. The script checks file-ID/map/area
collisions and the DEV SQL overlay, string bounds, geographic bounds and
routing fields, and preserves all old server records/strings. Independent
review confirmed the staged content and backup. The reviewed candidate was
installed into DEV with the server stopped, then restarted. Backup:
`work/client-overlay-r3/server-validated/WorldMapArea.before.dbc`.
Installed candidate hash:
`07722540733928e9cedadf7b9eb1d3d7acde50b16e138abf2f7fa0551b3d2c0b`.
No core, SQL, terrain, VMap or MMap changes were needed for cartography.

**Pending in-game:** automatic selection with M, player-marker placement,
indoor minimap alignment and transitions, outdoor tile seams, original map
regressions. Check the well and large rooms and test enUS/esES. If selection
fails, record .gps and `GetMapInfo()`/`GetCurrentMapDungeonLevel()` after
`SetMapToCurrentZone()`; do not call structural validation a render test.

## Exterior model artifacts: revision 2

**User-observed:** after installing the coordinated revision-1 overlay, crypt
entry and exploration work. The screenshot `/home/dev/artifacts.png` shows
numerous small blue/white missing-resource markers outside the crypt.

Cause established in the ADT data: the initial converter shortened `.mdx`
names to `.m2` in MMDX without recalculating MMID byte offsets. In the six
tiles, 465 of 474 MMID slots no longer point to the beginning of a name;
e.g. a lookup starts with `orld\\...` instead of `world\\...`. Checking that
every enumerated filename existed did not validate the indirection table.

`tools/adt_refs.py` now validates and remaps name starts, preserving slot
identities including repeated/nonsequential offsets; `tools/adt_convert.py`
rebuilds MMID whenever it transforms MMDX. Five unit regression tests pass:
shorter extensions with reordered/repeated slots, invalid start, unterminated
name, changed table shape and truncated offset.

`tools/build_crypt_refs_fix.py` repairs the existing revision-1 archive using
the original Turtle MMID/MMDX tables as the source of slot identity. Only the
MMID bytes in six ADT change. All 4,123 MDDF placements resolve to their
original model after the expected extension transformation; all 296 distinct
model paths exist in the 335 asset index. Every other file in T, including
WMO root/groups, DBCs and WDT, is byte-identical to revision 1. Both coordinated
Z copies are unchanged. MPQ extraction round-trip verifies every payload.

```sh
python3 -m unittest discover -s tools -p test_adt_refs.py
python3 tools/build_crypt_refs_fix.py --output work/client-overlay-r2
```

The output directory must be fresh. Final T:
`work/client-overlay-r2/Data/patch-T.MPQ`, SHA256
`6785296c4b54feb4ca2dc2bc918b6a9580812af118cd1f896edbb90d3cb13521`.
Installation/rollback: `work/client-overlay-r2/INSTALL.md`. A playing client
already on the coordinated revision-1 Z copies only replaces T, with WoW
closed; no change to source/reference clients was made.

Fresh VMap extraction/assembly and MMap generation ran in
`work/server-data/crypt-refs-r2`. Independent review confirmed all generated
map-800 VMaps/MMaps match revision 1 and runtime byte-for-byte, all 405
serialized collision-model dependencies exist and match runtime, and
`Tw800Crypt.wmo.vmo` is unchanged. The VMap extractor uses enumerated MMDX
indices directly, which explains why server collision had not shown the
client's MMID defect. No server redeployment/restart was necessary for r2.
The pre-existing absent MMap tile 35_52 remains outside this fix.

Independent review passed. Visual disappearance of the markers with revision
2 is **pending the next user test**, not claimed from binary validation.

## Confirmed revision-1 hash: conflict in the newly supplied client snapshot

The user confirmed revision-1 SHA256 on a **different Linux playing client**
and reported the same barrier. The user then refreshed `/home/dev/wow-335`
with an exact copy of that client. This is an explicitly supplied snapshot,
not a permanent synchronization guarantee. The previous stale-VM-copy finding
did not establish what the user was playing and must not be used to dismiss
their test.

Inspection of all 38 MPQs in the refreshed snapshot found conflicting map-800
ADT in root `Data/patch-Z.mpq` and `Data/esES/patch-esES-Z.MPQ`. In both, the
four relevant ADT still reference the original crypt WMO. Root Z also affects
enUS. No other tw800crypt overrides, map loose files or .MPQ directories were
found. Static analysis of this snapshot's Wow.exe patch enumeration and
priority assignment establishes root Z wins over root T. The extractor's
forced-last T load does not reproduce that client resolution.

Both Z archives also contain a map-800 Map.dbc row incompatible with the pilot.
Therefore merely supplying a correct T hash is insufficient; DBC and terrain
shadowing must both be resolved.

`tools/build_pilot_overlay.py` builds **copies only** in
`work/client-overlay-r1/`. Each Z copy removes the six map-800 ADT, WDT and
stale `KarachanCrypt.wdl`; its Map.dbc retains all 135 non-800 rows byte-for-byte
and replaces only row 800 with the pilot's row (preserving the original string
block and appending needed strings). All other archive entries are verified
content-identical: 40 root-Z entries and 24 esES-Z entries. AreaTable and
MapDifficulty do not occur in those Z archives. T remains byte-identical to
revision 1. Original MPQ hashes before/after match; no client installation was
modified. Eight negative/integrity checks and independent review passed.

Installable files (exact relative paths):

| Path | Output SHA256 |
|---|---|
| Data/patch-T.MPQ | 1455f5576b11c8ea53187488643f37970ec1798ce07483cdebf4c962d57f5229 |
| Data/patch-Z.mpq | cad32e8e64b89c862b857171fa413557c78e11f04aa2274c2d1af19571a3a022 |
| Data/esES/patch-esES-Z.MPQ | 25708c1a31b5532f111222007861e7bd50aad2beff24b40a27d5331c48958b50 |

Read `work/client-overlay-r1/INSTALL.md` before installation. Back up the
playing client's original files **outside Data**, check source hashes against
`report.json`, then install the three copies at their exact paths. If the
source hashes differ, rebuild/re-audit rather than applying snapshot-specific
Z copies. Rollback restores all pre-installation archives together.
Manual traversal after this conflict resolution remains pending. No additional
collision geometry was removed for this packaging correction.

## Follow-up barrier report: verify deployed client before changing geometry

User GPS at the barrier: map 800, instance 2, phase 1;
(-11068.141,-1825.4854,60.156975), orientation 1.6438121, indoors.
GroundZ 76.81083; FloorZ 60.155922; Map/VMap/MMap present at that point.

Transforming by crypt MODF 571057 gives local coordinates
(19.014858995,3.566248167,-11.707168372). The frontal face of the removed
box is ~0.360248 units forward (original triangle 802); its far face is
~4.250399 units forward (triangle 798). A 10-unit forward prism, ±0.5
units wide and 0.1–2 units above the feet, intersects those faces in the
original and none in Turtle or revision 1. Vertical geometry predicts
FloorZ 60.1559104, consistent with the user's measurement. These are static
geometry checks, not a live-client collision trace.

Deployment discrepancy observed: `/home/dev/wow-335/Data/patch-T.MPQ`
still has SHA256
`105f09f494cfe0432bc407f7aa733d5fa4394f1995c63469b09d65ed10d08eb1`;
it references the original WMO and lacks the tw800crypt family. It is NOT
revision 1. The artifact hash expected for revision 1 remains
`1455f5576b11c8ea53187488643f37970ec1798ce07483cdebf4c962d57f5229`.
This identifies the stale VM client copy, not which copy the user is running.
Runtime Tw800Crypt.wmo.vmo and 800_35_52.vmtile compare byte-identical to
the revision-1 extraction. Next action: verify the actual playing client's
patch hash and relaunch before removing any further geometry.

Additional converter defect discovered separately: the inherited ADT
converter rewrites MMDX names but does not recalculate MMID string offsets.
This requires a separate repair and full reference validation; do not
describe the initial model-reference existence check as proof of valid
placed-model references. It does not explain retaining the precise WMO
box that revision 1 removes.

## Invisible stair barrier: revision 1 (2026-10-19)

**User-observed in game:** teleport now enters map 800, instance 2, at
(-11210,-1610,220). `.gps` reports zone/area 5086, GroundZ/FloorZ 160.61644,
Map/VMap/MMap present at that point. User could inspect the copied Deadwind
Pass surroundings, but encountered an invisible barrier descending the crypt
stairs. Thus access is demonstrated; crypt traversal is **not** validated.

Binary comparison found WotLK `MD_Crypt_D_000.wmo` (`stairs`) contains an
extra collision-only box absent from Turtle: triangles 792–803, material 255,
local bounds (14.772541,3.926101,-12.425611) to
(23.687963,7.811986,-2.050285). Existence of an asset at the same filename
does **not** establish geometry/collision equivalence.

Revision 1 creates a WotLK-native variant with only those faces removed:
`World\\wmo\\Custom\\Turtle800\\tw800crypt.wmo` plus all 19 groups.
`tools/crypt_collision_fix.py` preserves the root and groups 001–018 and
rebuilds MOVI/MOPY/MOBR/MOBN in group 000. Vertex data and rendering batches
are preserved. The remaining stairs triangles match Turtle by coordinates
and winding. The root's pre-existing MOHD doodad-count discrepancy (658
declared vs 641 actual) is documented in the generated report, not repaired.

`tools/build_crypt_fix.py` changes only the MWMO string in four ADTs, using
an equal-length (41-byte) path so MWID and offsets remain unchanged. Unique
basename is essential because the VMap extractor flattens model filenames.
It packages 30 files, verifies each by MPQ round-trip, and preserves the
existing DBCs including MapDifficulty ID 756. No Blizzard model pathname is
overridden. This is a **minimal barrier fix**, not a full Turtle WMO port.

Rebuild and geometry check:

```sh
python3 tools/build_crypt_fix.py \
  --base work/patches/patch-T-difficulty-fixed.mpq \
  --output work/crypt-fix/revision-1
python3 tools/check_crypt_passage.py \
  work/crypt-fix/revision-1/sources/__home__dev__wow-335__Data__common-2.MPQ__World__wmo__Dungeon__MD_Crypt__MD_Crypt_D_000.wmo \
  work/crypt-fix/revision-1/wmo/World/wmo/Custom/Turtle800/tw800crypt_000.wmo
```

Output directories must be fresh. The local-space segment (19,3,-7) to
(19,9,-7) intersects original faces 798/803 and zero corrected faces.
This is **geometry validation**, not a live-server LoS or movement test.

Final client artifact: `work/crypt-fix/revision-1/patch-T.MPQ`
SHA-256: `1455f5576b11c8ea53187488643f37970ec1798ce07483cdebf4c962d57f5229`.
Install as `Data/patch-T.MPQ` in the separate test client, replacing the
previous pilot patch there, never patch-Z. Source clients were not changed
by this revision.

VMaps were re-extracted/assembled in fresh
`work/server-data/crypt-collision-r1`; MMaps regenerated there using the
existing terrain maps (heights unchanged). The 35_52 vertex-budget failure
persists. Independent review verified the MPQ and WMO structures and found
a pre-existing missing VMap dependency `Zulgurub.wmo.vmo` in runtime.
Deployment copied map-800 VMaps/MMaps, `Tw800Crypt.wmo.vmo` (case-sensitive)
and that missing native dependency, with DEV stopped, then restarted DEV.
Previous map-800 runtime files are backed up under
`work/server-data/crypt-collision-r1/runtime-before/`.

**Next manual test:** relaunch with revision-1 patch, re-enter map 800,
disable flight before reaching the stairs and try descending normally.
Record `.gps` and screenshots at any remaining barrier. The separate
instance is intentional for the pilot; an exterior-world entrance and
continuous access to map 0 have not been implemented.

## Pilot access failure and correction (2026-10-19)

The first user test failed with “Normal difficulty mode is not available for
Karazhan Crypt”. Startup and file generation did **not** validate entry to the
map; the pilot remains pending in-game validation.

Cause: the generated MapDifficulty row used ID 754 (map 800, difficulty 0).
DEV SQL `mapdifficulty_dbc` already owns ID 754 for map 533/difficulty 2
(Naxx40), and 755 for map 249/difficulty 2 (Onyxia). `LoadDBC()` loads SQL
after the file; `DBCDatabaseLoader` replaces records by ID. Thus SQL hid the
pilot row before `sMapDifficultyMap` was constructed.

Correction: `tools/merge_pilot_dbc.py` now uses ID 756, checked against the
base DBC and current DEV SQL. The server DBC was regenerated and deployed,
then DEV was restarted. A read-only reconstruction of the file + SQL overlay
asserted 756=(800,0), 754=(533,2), 755=(249,2). Independent review confirmed
the diagnosis. This is not an in-game entry test.

Updated client artifact: `work/patches/patch-T-difficulty-fixed.mpq` (install
as `Data/patch-T.MPQ` in a separate test client). No source-client file was
changed for this correction.

The earlier teleport instructions also swapped world axes and omitted the
MCNK base height. The first MCNK of tile 35_53 stores world origin
(-11200, -1600) and base height ~162.24. A provisional aerial inspection
point is (-11210, -1610, 220), map 800; floor/ceiling safety is not verified.
The exterior crypt door/entrance portal has not been integrated.

## Server-side validation (performed 2026-10-18/19)

### DBC merge

- `merge_pilot_dbc.py` produced `Map.dbc` (135 → 136 records) and
  `AreaTable.dbc` (2358 → 2359 records) with map 800 / area 5086, enUS + esES
  names populated. Re-parsed with `dbc.py` to confirm the rows and field counts.
- `map_extractor` re-extracted the DBC set from the integrated client and the
  output `Map.dbc`/`AreaTable.dbc` contain map 800 / area 5086 (verified by
  parsing the extracted files).

### Terrain extraction

- `map_extractor -e 1` (with `patch-T.MPQ`) produced 6 tiles
  `maps/800xxxx.map` for KarazhanCrypt with no "Error loading" diagnostics
  (after fixing the MCIN offset to the fixed 0x54 position the extractor
  hardcodes).

### Collision (VMaps)

- `vmap4_extractor --only 800` + `vmap4_assembler` produced
  `vmaps/800.vmtree` and 6 `.vmtile` files.

### Navigation (MMaps)

- `mmaps_generator 800` produced `mmaps/800.mmap` and 5 `.mmtile` files. Tile
  `[35,52]` was skipped by Recast ("Too many vertices! 71281 out of 65535").

### Server startup

- `worldserver` restarted cleanly after the DBC/maps/vmaps/mmaps were deployed.
  `WORLD: World Initialized ... ready`; no errors attributable to map 800 or the
  merged DBCs (only pre-existing warnings: process-priority, `spell_icehowl`,
  one vendor `ExtendedCost` notice).

## Commands used

```text
map_extractor -i <client> -e 1|-e 2
vmap4_extractor -d <client>/Data --only 800 && vmap4_assembler
mmaps_generator 800
```

## Not yet performed / pending

- In-game visual validation (client load, terrain, textures, WMOs, minimap) —
  blocked: no Wine/Windows client on the DEV VM. Must be done manually.
- Character teleport / movement / collision / LoS verification in-game.
- MMaps tile `[35,52]` regeneration (needs tile simplification or a Recast
  vertex-budget workaround).
- Regression sweep over original maps after the DBC/map changes (not yet run;
  the changes are additive but must be confirmed in-game).

## Integrity

- `work/compare/mpq-hashes.txt` holds SHA-256 of the source MPQs (reproducibility
  anchor). `patch-Z.mpq` unchanged (hash preserved; see client `Data/`).
