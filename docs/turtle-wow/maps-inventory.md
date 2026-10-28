# Turtle WoW maps — inventory

Preliminary inventory of custom geography identified in the Turtle snapshot and
its port status. Initial observations come from the clients at
`/home/dev/wow-turtle` (source, Vanilla 1.12.1 build 5875, Turtle 1.18.1) and
`/home/dev/wow-335` (destination, WotLK 3.3.5a build 12340) on 2026-10-18, using
MPQ listings + DBC parsing + ADT header parsing. Later pilot acceptance is scoped
explicitly below. This is not an exhaustive inventory of all custom geography:
the 57 Map.dbc records enumerate source map rows, not every modified region,
common continent tile, asset or cartographic change.

Status vocabulary: `pendiente` / `inventariada` / `convertida` /
`integrada cliente` / `integrada servidor` / `validada` / `completada`.
These are descriptive labels, not a completed formal phase checklist. Here
`inventariada` means a source record/region was identified; it does not imply
complete tile/dependency bounds or a destination ID allocation. `Validada` must
state the tested scope; no global `completada` claim is established.

## How this inventory was produced

- `tools/mpq.cpp` (StormLib) lists/extracts MPQs.
- `tools/dbc.py` parses WDBC.
- `tools/adt.py` parses ADT headers (area IDs, textures, models, WMOs).
- `tools/mpq_priority.py` selects copies using a static assumed priority order
  over cached listings. That order is not end-to-end verification of actual
  game-client resource selection.
- `tools/extract_tiles.py` extracted the 175 new continent tiles and scanned
  their area IDs.

The initial extracted Turtle DBCs come from `patch-9.mpq` (Map, AreaTable,
WorldMapArea, WorldMapOverlay, LoadingScreens). Initial 335 DBC extracts come
from `patch-eses-3.mpq`
(Map), `patch-esES-N.MPQ` (AreaTable, WorldMapArea), `patch-eses.mpq`
(WorldMapOverlay). These provenance notes describe the initial audit, not every
subsequent pilot overlay or the user's active playing client. Local evidence
under `work/` is not a versioned source-of-truth manifest; present scripts and
`tools/crypt_portals.json` carry technical pilot decisions. Check input/source
availability before claiming clean-clone reproducibility.

## Client facts

| Fact | Turtle (source) | 335 (destination) |
|---|---|---|
| Base build | 5875 (Vanilla 1.12.1) | 12340 (WotLK 3.3.5a) |
| Turtle/labels | 1.18.1 | ChromieCraft-derived + patch-Z |
| Locale | enUS (server: Nordanaar) | esES active (enUS present) |
| Measured MPQ headers | patch9: 32 bytes / format field 0 | patch-Z: 32 / 0; common-2 and patch-enUS-3: 44 / 1 |
| Map.dbc records | 57 | 135 |
| AreaTable.dbc records | 1481 | 2358 |
| Terrain ADT version | sampled MVER 18 | sampled MVER 18; optional chunks vary |

MPQ signature alone does not identify the format version. Matching ADT MVER
does not establish alpha/liquid compatibility; see [compatibility](compatibility.md).

## New continent tiles (Turtle-only, 175 total)

The listing-based comparison found 121 Kalimdor + 54 Azeroth source-only ADT
paths, size > 0, with copies selected under the tooling's assumed patch priority.
This is a measured result of that comparison, not proof of actual client
precedence, all custom geography, or a complete diff of modified common tiles.
Original continent modifications (including regions absent from this new-tile
set) still require comparison against their native 335 counterparts.

| Map | Scanned ADTs / area evidence | Supported attribution |
|---|---|---|
| Kalimdor | 43_5, 43_6, 44_5, 44_6: area 5024; nearby 5027 sea | Icepoint Rock / North Sea samples |
| Kalimdor | 45_13–19: area 5642 and subareas | Moonwhisper Coast samples |
| Kalimdor | 45–47 × 31–33: area 5536 and subareas | Blackstone Island samples |
| Kalimdor | 44–45 × 45–49; 46 × 46–49: area 5121 and subareas | Tel'Abim subset (14 ADTs) |
| Azeroth | 24_45–49 and 25_45–46: area 5561 and subareas | Balor open-world samples, not Gilneas |
| Azeroth | 23_54, 24_56: area 409 | Lapidis Isle samples |
| Azeroth | 24_56–59, 25_59, 26_59: area 408 | Gillijim's Isle samples |

Tile names use filename X_Y, not world-coordinate axes. The rows above report
area-scan evidence, not full rectangular region ownership. Earlier speculative
coast/cluster labels based on coordinate offsets are withdrawn. Empty area-scan
results remain unresolved, not evidence for a named zone or unused tile. See
`work/compare/newtiles-areas.tsv` for all 175 paths and per-tile area observations.

## Custom regions (from Turtle WorldMapArea.dbc)

### On shared continents (Kalimdor / Azeroth)

The following bounds are **source WorldMapArea footprints in world coordinates**,
not precise ADT merge extents or proof that all tiles inside are custom. Source
area IDs are not assigned destination IDs for pending regions; the high-elf
assignments are recorded in [id-mappings.md](id-mappings.md#altos-elfos-en-mapa0).
Compare modified/common native tiles as well as additions before selecting a
region's merge set.

| Region | Map | Area ID | Bounding box (world coords) | Type | State |
|---|---|---|---|---|---|
| Mount Hyjal | Kalimdor (1) | 616 | (3983,-4286)–(6125,-1080) | new open zone | inventariada |
| Tel'Abim | Kalimdor (1) | 5121 | (-9371,-8406)–(-7184,-5179) | new island | inventariada |
| Moonwhisper Coast | Kalimdor (1) | 5642 | (4963,-9210)–(10204,-1354) | new coast | inventariada |
| Icepoint | Kalimdor (1) | 5024 | (13330,-7203)–(14405,-5595) | new island | inventariada |
| Blackstone Island | Kalimdor (1) | 5536 | (-866,-8746)–(799,-6274) | new island | inventariada |
| Gilneas | Azeroth (0) | 5179 | (-2801,-413)–(-359,3253) | new open zone | inventariada |
| Gilneas City | Azeroth (0)/map 815 | 5208 | map 815 interior | new city/instance | inventariada |
| Thalassian Highlands | Azeroth (0) | 5225 | (2891,-4087)–(4952,-1005) | new open zone | [integrada regular/servidor; validación estructural, no visual/gameplay](high-elf-maps.md) |
| Alah'Thalas | Azeroth (0) | 2040 | (3931,-3637)–(4907,-2169) | new settlement | [integrada regular/servidor; validación estructural, no visual/gameplay](high-elf-maps.md) |
| Gillijim's Isle | Azeroth (0) | 408 | (-14576,1344)–(-12529,4436) | new island | inventariada |
| Island of Lapidis | Azeroth (0) | 409 | (-12959,2032)–(-11043,4933) | new island | inventariada |
| Grim Reaches | Azeroth (0) | 5602 | (-6488,-7459)–(-2904,-2072) | new coast | inventariada |
| Balor (open) | Azeroth (0) | 5561 | (-9645,1630)–(-7577,4728) | new zone | inventariada |
| Northwind | Azeroth (0) | 5581 | (-8484,-983)–(-6327,2258) | new coast | inventariada |

### Additional / reused source map records

These records identify candidates, not a certified count of wholly new maps.
532/533 collide with native raids; Vanilla-era reused records also require
semantic comparison. Most destination allocations are pending.

| Map ID | Directory | Areas (sample) | Type | State |
|---|---|---|---|---|
| 532 | Karazahn | Lower Karazhan Halls | raid | inventariada |
| 533 | Stratholme Raid | Naxxramas, The Upper Necropolis | raid | inventariada |
| 800 | KarazhanCrypt | Karazhan Crypt | dungeon | **validada: practical geographic pilot**; bounded acceptance below |
| 801 | Moomoo | Moomoo Grove | test/fun | inventariada |
| 802 | Grove | Crescent Grove, Vilethorn Scar | dungeon | inventariada |
| 807 | EmeraldSanctum | Emerald Sanctum | raid | inventariada |
| 808 | Hateforge | Hateforge Quarry | dungeon | inventariada |
| 813 | Winterveil | Winter Veil Vale, Icepaw Village | event map | inventariada |
| 814 | Karazahn40 | Upper Karazhan, The Rock of Desolation | raid | inventariada |
| 815 | Giln | Gilneas City, Greymane Tower | city/instance | inventariada |
| 816 | Dragonmaw | South Seas, Kamio, Kontsuma, … | open zone/instance | inventariada |
| 817 | HighElfPVP | Sunstrider Court | battleground | inventariada |
| 818 | Balor | Stormwrought Ruins | instance | inventariada |
| 819 | Timbermaw | Timbermaw Hold | raid | inventariada |
| 820 | MooCanyon | Windhorn Canyon | dungeon | inventariada |
| 821 | netherstormbg | Thorn Gorge, … | battleground | inventariada |
| 822 | FrostmaneCaverns | Frostmane Hollow | dungeon | inventariada |
| 27 | Sunnyglade | Sunnyglade | battleground | inventariada |

Other source directories such as EmeraldDream (169), CavernsOfTime (269),
SchoolofNecromancy and ScarletCitadel require their own content/dependency
audit. 169 and 269 already exist in native 335 Map.dbc. This selected table is
not an exhaustive map-to-custom-content classification of the 57 source rows.

## Provisional listing counts by source directory

The historical counts below mixed ADT/WDT/WDL entries across patch listings,
including duplicates. They are **not deduplicated ADT counts**, effective map
coverage, or final import sizes. Retained only as preliminary listing evidence:

EmeraldDream 312 · CavernsOfTime 80 · Sunnyglade 66 · Karazahn40 39 ·
netherstormbg 37 · Grove 36 · SchoolofNecromancy 29 · Stratholme Raid 26 ·
Winterveil 17 · Giln 17 · HighElfPVP 20 · Timbermaw 10 · MooCanyon 10 ·
Hateforge 10 · FrostmaneCaverns 10 · Dragonmaw 10 · Balor 10 · Karazahn 11 ·
KarazhanCrypt 8 · ScarletCitadel 6 · EmeraldSanctum 5 · Moomoo 3 · … (full list
in `work/extract/listings`).

For the actual pilot, the established set is **KarazhanCrypt: 6 ADTs + 1 WDT**;
the historical listing total 8 must not be used as its ADT count. Balor was an
earlier discarded pilot candidate (9 ADTs + WDT), not the implemented pilot.

## Pilot status and Tel'Abim follow-up evidence

KarazhanCrypt map800 / area5086 is integrated in client and server. The user
accepted exploration, cartography/manual Spanish artwork, loading screen,
walking entrance/exit, temporary-rabbit movement and short wall/between-floor/
water-well-edge checks. This is practical geographic acceptance, not exhaustive
navigation: the offline suite retains 410 partial/disconnected combinations.
See [validation](validation.md) and [navigation](navigation.md); the pilot does
not certify other maps or an ADT liquid converter.

For Tel'Abim, a read-only audit identified a **verified subset of 14 local ADTs**
under `work/extract/turtle/newtiles`: `kalimdor_44_45` through `_44_49`,
`_45_45` through `_45_49`, and `_46_46` through `_46_49` (all `.adt`). Each
contains MCLQ. Their direct references resolve in the cached 335 index except
for one WMO family:

`World\wmo\monoman\utari\utari_house_03.wmo`

It is referenced by `kalimdor_45_48.adt`; Turtle patch3 listings contain its
root and group000. Acquiring and auditing that complete family and its transitive
dependencies is follow-up work. Availability in the source does not prove
destination compatibility. These findings do not establish the whole island's
perimeter/halo, actual end-to-end MPQ precedence, asset fidelity or merge readiness.
MHDR is now corrected. Validate Tel'Abim's liquid types, masks/heights and
client/server behavior independently: high-elf source-MH2O preservation is not
proof of Tel'Abim MCLQ rendering or a general MCLQ→MH2O converter. See
[compatibility](compatibility.md).

## Open questions / next audit steps

1. Complete source coverage: classify all 57 Map records and compare common
   continent ADTs, not just the 175 source-only paths. Reconcile WDT MAIN,
   per-MCNK areas, WMO placements and WMA footprints; do not rely on a presumed
   WDT `mpin` area table or speculative renumbered-Azshara attribution.
2. Enumerate WMO/M2/BLP dependencies of the new tiles and classify which are
   already present in 335 vs Turtle-only (reuse vs convert).
3. Map the minimap / WorldMap overlay assets (`Interface\WorldMap\*`,
   `Textures\Minimap\*`) for the new regions.
4. Determine loading-screen and `AreaPOI`/`WorldSafeLocs` additions.
5. Produce per-region deduplicated effective file sets, boundaries/neighbor
   seams, unresolved references and explicit destination ID decisions. Keep
   preliminary observations separate from converted/integrated/validated results.

## Related documents

- `compatibility.md` — format gaps (Vanilla 1.12 → WotLK 3.3.5) and strategies.
- `id-mappings.md` — the authoritative ID allocation register.
- `../project/features/turtle-wow-maps.md` — existing port feature contract.
