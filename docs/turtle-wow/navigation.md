# Karazhan Crypt — navigation and collision validation

## Data-only fix for the missing tile

Map800 originally had five MMap tiles. Generator tile35,52 failed with
71,281 combined polygon-mesh vertices; the native generator/Detour check
rejects counts >=0xffff, so the accepted maximum is65,534. This is not the
detail-vertex budget and is not fixed by increasing polygon-reference width.
Do not disable the check or change Detour's vertex-index format.

The selected scoped profile changes only `maxSimplificationError` from0.8
to0.9 for this tile. It preserves slope60°, height6, climb4, radius2,
2000 vertices/map edge,80/subtile edge and voxel size approximately0.266667.
There is no change to any global installed configuration, terrain or VMap.

Coordinate conventions are deliberately explicit:

| Consumer | Value |
|---|---|
| Generator CLI/ADT | `35,52` |
| Config `tilesOverrides` key | `"52,35"` |
| Server MMap/terrain filename | `8005235.mmtile` / `8005235.map` |
| VMap filename | `800_35_52.vmtile` |
| Native StaticMapTree load parameters | `52,35` — formatter reverses them |

`tools/crypt-nav-800.yaml.in` is the explicit profile. The wrapper
`tools/crypt_nav_generate.py` substitutes a new isolated output directory and
the trial error (default0.9). It always generates only map800 and never
installs files. It records all input geometry/config/binary hashes and checks
input files remain unchanged. Fresh outputs prevent stale tile reuse.

Measured candidates on the same geometry:

| Simplification | Tile vertices | Polygons | Result |
|---:|---:|---:|---|
| 0.8 | 71,281 | — | No tile; native limit reproduced |
| 0.85 | 63,883 | 39,814 | Generates;22 surface-follow failures in the diagnostic suite |
| 0.9 | 54,745 | 33,379 | Generates; all350 complete diagnostic queries pass surface/LoS checks |
| 1.0 | 44,538 | 27,085 | Generates; not selected because0.9 suffices |
| 1.2 | 36,958 | 22,583 | Generates; not selected |

Generation is not monotonic acceptance by file existence:0.85 was not selected
merely because it fits. The0.9 tile has additional budget margin and better
surface-follow results under the same measured connectivity. All other five
tiles and `800.mmap` remain byte-identical to the existing data.

## Native offline validation

`tools/crypt_nav_probe.cpp` links against the checkout's already-built Detour,
VMap/StaticMapTree and common libraries. It checks the actual native MMap
version/header and adds tiles through Detour. Every required VMap tile must
exist before loading: native LoadMapTile can otherwise report success for an
empty/missing tile, which would make naive LoS tests misleading.

The tool uses world XYZ -> Detour `{Y,Z,X}` and the native VMap coordinate
converter. It checks floor heights and LoS against the collision data, not a
Python-only interpretation of it. Sample points are real polygon centroids
with WMO root3833/group identity and matching native floor, not averaged
coordinates guessed to be walkable. Actual `.gps` stair floor60.156513 matches
the native VMap query.

20 points (18 WMO groups plus arrival/barrier references) produce760 ordered
point-pair/filter queries. The filters distinguish ground from ground+water
and exclude magma/slime/steep areas. `findPath` must reach the end polygon
without partial/out-of-nodes/buffer flags. Complete paths are then followed
on the native surface in0.4-unit steps with corridor-prefix maintenance,
detail-height lookup and bounded edge reprojection (XY<0.01, Z no more than
native climb). Body-height rays at floor+1.5 are checked per step.

Selected0.9 results:350 complete queries,195,858 surface steps, zero sampled
surface failures and zero VMap-blocked sampled segments.4,927 exact-edge height
fallbacks are recorded, not hidden. Before adding the tile, only12 of these
queries completed; all remain available. This does not mean350 unique routes
or350 independent room traversals: direction and filter are part of the suite.

Controls distinguish valid detours from bad shortcuts:

* Almost identical XY in two hallway floors26 units apart: complete174.5-unit
  staircase detour, direct LoS blocked, no sampled intersection.
* Well room versus ossuary floor69 units lower: no complete route and blocked
  LoS; the tool does not silently snap the floors together.
* Corrected stair passage: complete route, clear direct LoS and correct floors.
* Separate rooms: direct LoS blocked but a complete149-unit corridor route
  follows the doorway, with no sampled collision.

The query helper is diagnostic, **not execution of a live Unit/PathGenerator**.
Its buffers and0.4 step differ from the movement generator. The inspected
Playerbots source uses148 path/point slots and4-unit smoothing steps; long
movements can require repeated pathfinding. Segment LoS is not a swept capsule
test. Dynamic gameobjects and module/unit behavior still require game tests.

## Remaining disconnected regions — do not hide them

410 query/filter combinations remain partial/disconnected. Ground queries
connect the arrival, stairs, well room, five spiral halls, large vault,
massgraves and unrepentant-room samples. Ground+water additionally connects the
sinkhole sample. Other components contain underwater/upsidedown samples,
arched hall/water ramp (with ossuary connected by the water filter), and the
collapsed-room sample. Group18820 (well) has no selected ground-nav sample.

These are **not certified as globally navigable**. Sampling, physical access,
vertical drops and submerged transitions require separate inspection. No
arbitrary off-mesh link, collision removal, clearance reduction or forced
cross-floor connection was added to make statistics look complete.

## Build/test artifacts and reproduction

Final generation and evidence:
`work/server-data/crypt-navmesh-r1/`.

```sh
python3 tools/crypt_nav_generate.py --output work/server-data/crypt-nav-new --all-tiles
python3 tools/build_crypt_nav_probe.py
```

The generator needs the verified static geometry under
`work/server-data/crypt-refs-r2/{maps,vmaps}`. Source directories are linked as
read-only inputs by convention; the generator writes only its separate output.
Use the generated per-input hashes to detect changed source geometry.

Probe query files and point evidence are under `work/crypt-nav-probe/`.
`crypt_nav_queries.py` selects points from the probe's WMO-classified sample
TSV; `crypt_nav_report.py` checks route comparisons and controls and writes a
report containing both passes and residual limitations. The final run's
report is `work/server-data/crypt-navmesh-r1/validation.json`.

The selected new tile SHA256 is:
`20da70c08443295bcf916be3c1c8974b01534efa8de08b92d044d143cbe4e20e`.
Single-tile and complete-map regeneration produced the same new tile. Existing
five tiles/params were compared byte-for-byte before deployment. Independent
review rebuilt the native probe, repeated760 queries and controls, reproduced
the selected and alternative results, and approved the incremental deployment.

## DEV installation and reversal

The existing six files (five tiles + map params) were backed up under
`work/server-data/crypt-navmesh-r1/recovery/`. `before.json` records that the
new tile did not exist. DEV was stopped, **only** `8005235.mmtile` was added,
its hash checked and DEV restarted. No client, SQL, DBC, core or installed
generator-config changes were made. Queries against the actual runtime data
reproduce the four controls exactly.

Rollback: stop DEV, verify the added file still has the selected hash, remove
only `bin/mmaps/8005235.mmtile` and restart. Do not overwrite the other five
tiles or restore an invented earlier version of the previously absent file.

## Next in-game test: temporary passive follower

No NPCs were spawned by the offline tests. Use a GM character already **inside
map800**, on dry ground at the arrival, with flight disabled:

```text
.gm on
.gm fly off
.mmap loc
.npc add temp 721
```

Entry721 is the existing Rabbit template: civilian/non-aggressive, no explicit
AI/ScriptName and no ignore-pathfinding flag. The command uses a temporary
summon; it does not add a database spawn. Select that rabbit, walk a few yards
away, then run:

```text
.mmap path
.npc follow
```

Keep walking distances short at first and progress through dry rooms/spiral
stairs. Check obstacle detours, not just arrival near the player. `.mmap path`
uses the selected unit as source and player as destination; its output includes
the actual Unit PathGenerator path type and actual endpoint. Normal type is
bit0x01; incomplete0x04/no-path0x08/not-using-path0x10 are not the same success.
The command's visible waypoint summons expire after9 seconds.

For an LoS check, stop following with `.npc follow stop`, leave the rabbit in
one room, stand around a wall and run `.debug los` while keeping it selected.
An obstacle should block LoS while `.mmap path` can still route around the
doorway. Re-enable follow for the next short movement. Avoid water initially.

Do not try to have the rabbit cross the instance portal: player AreaTrigger
transfers do not transport an ordinary follower NPC between maps. Cleanup:
select **only the test summon**, then `.npc follow stop` and `.npc delete`.
The core removes an unsaved temporary creature without deleting a DB spawn;
it may log the expected not-saved-creature warning. Do not assume this summon
expires after120 seconds alive: its command uses corpse-despawn semantics.

On failure, record `.gps`, `.mmap loc` and `.mmap path`, plus a screenshot.
The user subsequently confirmed that the temporary rabbit behaves correctly
in game. This accepts the follower movement tested, not every possible room
connection. The user then reported the short wall, between-floor, and water /
well-edge checks all OK. These close the agreed practical pilot checks.
Exact locations and exhaustive connections were not recorded; deep swimming,
well descent and all disconnected query components are not thereby certified.
