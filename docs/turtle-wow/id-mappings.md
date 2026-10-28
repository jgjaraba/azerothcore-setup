# Turtle WoW maps — ID mappings

Register of known geographic-port allocations, source IDs and collision rules.
An ID in a source DBC is not an allocation in the destination. Most future
regions still have **no destination mapping assigned**.

The initial evidence comes from the Turtle/335 snapshot extracts under
`work/extract/{turtle,335}/dbc`. These are local audit artifacts, not a versioned
allocation manifest. Present project sources include `tools/crypt_portals.json`,
the pilot DBC/cartography/loading builders and the custom SQL; inspect their
availability and tracking before claiming clean-clone reproducibility.

## Observed ranges and schemas

| Namespace / schema | Turtle source snapshot | 335 destination reference snapshot |
|---|---|---|
| Map IDs | max 822; 57 records | max 724; 135 records before pilot overlays |
| Area IDs | max **5735**; 1481 records | max 6456; 2358 records before pilot overlays |
| WorldMapArea IDs | observed 4–705 | audit each effective client/server baseline separately |
| Map.dbc fields | 42 | 66 |
| AreaTable.dbc fields | 25 | **36** |

Ranges describe snapshots, not reserved/free intervals. Locale and overlay
selection matter; client and server baselines can contain different records.
Field indices mentioned below are zero-based.

## Map collision register

| Turtle Map ID | Source directory | Destination status | Decision |
|---|---|---|---|
| 532 | Karazahn | occupied by native WotLK Karazhan raid | source port remap pending |
| 533 | Stratholme Raid | occupied by **WotLK Naxxramas** | source port remap pending |
| 169 | EmeraldDream | existing native Map.dbc record | semantic/content comparison and destination decision pending |
| 269 | CavernsOfTime | existing native Map.dbc record | semantic/content comparison and destination decision pending |
| 27 | Sunnyglade | absent from audited 135-row reference | candidate only; final collision audit and allocation pending |
| 800 | KarazhanCrypt | absent from that reference; now owned by the pilot | allocated below |
| other source IDs in 800–822 | see inventory | above audited native maximum, but not automatically free in project/runtime overlays | individual allocations pending |

The inherited directory spelling `Karazahn` and legacy `Stratholme Raid` name
are not evidence of unused slots. Never replace map 533 as an unused placeholder.
Maps 169 and 269 likewise cannot be treated as absent simply because their
Vanilla/Turtle use differs from WotLK.

## Area collision register

| Source area | Source name | Destination interpretation |
|---|---|---|
| 408 | Gillijim's Isle | record exists; audited enUS name field empty, esES name fields populated |
| 409 | Island of Lapidis | record exists; audited enUS name field empty, esES name fields populated |
| 616 | Mount Hyjal | existing native record; do not equate Turtle geography with WotLK Hyjal usage |
| 2040, 5225 | Alah'Thalas / Highlands | allocated on map0; see high-elf register below |
| 4012, 5024, 5121, 5179, 5536, 5561, 5581, 5602, 5642 and other custom areas | source region/subzone IDs | individual destination collision and semantic audit pending |

An empty name in one locale does **not** declare a row unused. Reuse vs remap
for 408/409/616 is unresolved. No blanket assertion that all other custom areas
are free is valid: compare every row and reference with the effective destination.
Source ADTs can carry inherited/stale Vanilla area IDs, so remapping requires
geographic interpretation rather than an unconditional identity map.

## Allocated pilot identifiers: KarazhanCrypt

| Namespace | Destination value | Binding / technical source |
|---|---|---|
| Map.dbc | **800** | `KarazhanCrypt`; `tools/merge_pilot_dbc.py` |
| AreaTable.dbc | **5086** | `Karazhan Crypt`, map 800; same builder |
| MapDifficulty.dbc / server SQL overlay | **756** | map 800, normal difficulty 0; same builder |
| WorldMapArea.dbc | **674** | map 800 / area 5086, internal name `KarazhanCrypt`; `tools/build_crypt_cartography.py`, `tools/stage_crypt_server_worldmap.py` |
| LoadingScreens.dbc | **511** | Turtle loading artwork; `tools/build_crypt_loading.py` |
| AreaTrigger.dbc + SQL trigger/teleport IDs | **900800 / 900801** | entrance / exit; `tools/crypt_portals.json`, `tools/build_crypt_portals.py` |
| gameobject_template entries | **900800 / 900801** | decorative portal templates; same access sources |
| gameobject GUIDs | **900800 / 900801** | portal spawns, phase 1 / spawnMask 1; same access sources |
| dungeon_access_template | **124** | map 800, normal, minimum level 55, no requirement rows; same access sources |

These values are allocations, not universal availability claims or a fresh
deployment audit. See [native access](crypt-portals.md),
[validation](validation.md) and `../project/CUSTOM-IDENTIFIERS.md` for related
ownership and recorded evidence.

### Cross-table invariants and collision lessons

- Pilot MCNK area IDs are mapped to 5086. Source tiles include inherited IDs
  4/8/10/19/33/41/42/73/121/…; the pilot's blanket single-zone remap is not a
  rule for future multi-zone regions.
- MapDifficulty **754 is occupied** by DEV SQL Naxx40 (map 533 / difficulty 2);
  755 belongs to Onyxia (249 / difficulty 2). SQL replaces file records by ID.
  The pilot uses 756; check both sources before every future allocation.
- WMA 674 retains Turtle geographic bounds. Client and server merges preserve
  their own independent baselines (audited 212 vs 108 records). Native routing
  fields use -1/0/0; no DungeonMap/DungeonMapChunk IDs were allocated for this
  single unnumbered plan. WMA row IDs are distinct from AreaTable IDs.
- LoadingScreens 511 was free in the audited native 91-row table (max 254).
  Map800 references it at **335 field 57**, not Turtle field 38. The target
  LoadingScreens row has four fields, HasWideScreen 0. It requires no server
  LoadingScreens SQL table. Root/locale Map.dbc copies must agree.
- Source access triggers 5008/5011 are adapted to 900800/900801; native Nagrand
  trigger 5008 is preserved. Trigger, GO entry and GO GUID are separate
  namespaces even when they share numeric values. MapID-sorted client trigger
  rows are required by the observed lookup; append-only existence is insufficient.
- Access builders accept identical owned reruns and reject conflicts. That
  guarded pilot behavior is not proof every initial DBC merger is generic or
  performs all required collision checks.

## Altos Elfos en mapa0

`tools/high-elf-map.json` defines the explicit mappings; the source-locked final
cartography deltas live in `client_patches/archive/source-inputs/high-elf-map/`.
These are map0 additions, with no new Map ID or gameplay SQL.

| Namespace | Source → destination | Preservation rule |
|---|---|---|
| AreaTable roots |2040→2040,5225→5225 | Alah'Thalas / Highlands on map0 |
| AreaTable colliding subareas |3881–3883→6500–6502 | native Outland3881–3883 remain untouched |
| AreaTable other subareas |5526–5535,5544–5546,5552–5555→same IDs | explicit identity map, not blanket range ownership |
| Area exploration flags |22 selected areas→3500–3521 | order is the explicit manifest mapping, not sorted destination IDs |
| WMOAreaTable records |18 selected source rows→60000–60017 | custom WMO roots6000–6002 only; inherited root4772/nameSet1 keys remain native |
| WorldMapArea |509→509,513→513 | original regional file tokens/bounds; independent baseline merge |
| WorldMapOverlay |9 selected rows→60000–60008 | source-ID-sorted allocation; see evidence `cartography-manifest.json` / `worldmap.overlay_id_mapping` |

AreaTable IDs, exploration flags, WMOAreaTable record IDs, WMO root identities
and WorldMapOverlay IDs are distinct namespaces. Numeric overlap does not make
them interchangeable. All newly remapped MCNK/parent/metadata references must
agree; preserving an old native record must not route a new map0 subarea to
Outland. Rebuilds recheck effective locale/client/server baselines and SQL;
the final deltas preserve native record and string-block prefixes.

See [geographic contract](high-elf-maps.md) and
[schema2 server installation](high-elf-server-data.md) for scope and limits.

## Allocation procedure for future regions

1. Enumerate source IDs and their references: maps, parent/subareas, difficulty,
   WMA/overlays, loading screens, WMO-area metadata, triggers and any required
   native-access SQL. Add other namespaces only if the geographic import uses them.
2. Audit effective client DBCs for all relevant locales, independent server DBCs,
   SQL overrides and project/core/module sources. Consult the project identifier
   register; a maximum ID or empty localized string is not a collision test.
3. Record explicit source→destination assignments and ownership before emitting
   data. Preserve all unrelated native records, strings and geographic references.
   Check record layout and ordering as well as ID membership.
4. Validate the merged file + SQL result, client/server bindings and coordinated
   archive precedence. Preserve conflict-aware rerun/rollback semantics and
   document validation scope.

The crypt and high-elf allocations above are settled here. Remaps for 532/533 and
assignments for other source maps/areas remain pending; neither the inventory's
names nor its world-coordinate footprints allocate destination identifiers.
