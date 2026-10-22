# Karazhan Crypt: native-access pilot

## Source contract

`tools/crypt_portals.json` is the versioned source for the two shapes,
destinations, portal visuals, access row and provenance. Builder:
`tools/build_crypt_portals.py`. Canonical generated SQL is retained in
`data/sql/custom/db_world/turtle_wow_crypt_access.sql` and must match generated
text exactly. The world manifest installs it after `turtle_wow_maps.sql`.
Both files preserve identical instance metadata; differing map800 metadata
fails closed rather than replacing an existing instance script or settings.

Source evidence is Turtle patch9 AreaTrigger.dbc and public Tortoise SQL at
commit `4a9b6d564b685aaf63eb056f1f0e6d6adc9e46b4`, not a claim about current
official Turtle production. The manifest retains source coordinates and measured
floor/barrier bounds so adaptations are explicit:

| Portal | Trigger | Destination |
|---|---|---|
| Entrance900800 | map0 `(-11068.14,-1826.3,62.2)`, box1×8×6, o1.59698, radius exactly0 | map800 `(-11068.1,-1806.4,52.85)`, o1.5 |
| Exit900801 | map800 `(-11068.2998046875,-1814.06005859375,53.97779846191406)`, sphere radius3 | map0 `(-11068.9,-1828.6,60.4)`, o3.1 |

Turtle entrance5008 is beyond the native map0 barrier. The adapted box sits
wholly before its Y minimum -1825.236721 (box maximum Y approximately -1825.6954).
Map0 geometry/collision is not modified. Exit volume is authentic Turtle5011.
The arrival height changes from52.7 to52.85, above measured ground52.7424938;
return height changes from60.26 to60.4, above ground60.2611202. These are small
clearance adaptations, not gameplay-validated landing claims. Both arrival
points are outside the opposite trigger, including a conservative1.5-yard
expanded-volume check. WotLK Nagrand trigger5008 remains untouched.

Visuals clone the minimal native188096 configuration: type5/display672,
Data1=1, Data6=-1, other Data fields0, empty AIName/ScriptName; scale1.6.
The native server display DBC resolves672 to InstancePortal.mdx. No Turtle
display IDs, imported model or portal scripts are used. Spawn GUIDs and template
entries are900800/900801, spawnMask1/phaseMask1/state1/animprogress255/300s.
Quaternions are `(0,0,sin(o/2),cos(o/2))`. Entrance visual ground is60.2;
exit visual retains Turtle53.9778. Entrance zone/area41/2563 and exit5086/5086
are descriptive spawn metadata, independent of trigger/teleport decisions.

Access124 uses map800/difficulty0/min55/max0/ilvl0. No key, quest or requirement
rows are inserted. Native map admission enforces this gate; decorative GOs do
not teleport. Existing `instance_template(800,0,'',0)` is required and preserved.
This core loads server shapes from SQL `areatrigger`; corresponding client DBC
records are needed to emit native trigger messages. A server DBC alone does
not activate these portals.

## Build and artifact validation

From the setup root:

```sh
python3 -m unittest discover -s tools -p test_crypt_portals.py -v
scripts/apply-db-world.sh --validate
python3 tools/build_crypt_portals.py
```

Output defaults to a **new** `work/client-overlay-r4.1`; use `--output` with a
different new work directory for reproduction. The builder only stages files
under work and queries DEV using read-only transactions. Required tools are
Python standard library, `tools/mpq` (StormLib), `rg`, and the configured MySQL
`azeroth-dev` login path. It does not deploy, reload or restart services.

Approved input T SHA256:
`175a802e1ff52f4210c429b652e05c170e8dfadca7dbd312bc5b6bf1386bdfd3`.
Native AreaTrigger source is the supplied WotLK enUS patch3 snapshot with
SHA256 `c043300ffae75d78374bcdde57c397ef8d07c2269d1d81d57acab44567d9866c`;
server baseline must be identical. Source directories are reference snapshots,
not evidence of the active playing installation.

Generated deliverables:

- `Data/patch-T.MPQ`: 69 resources. All68 approved resources are preserved
  byte-for-byte; only AreaTrigger.dbc is added.
- `Data/patch-Z.mpq` and `Data/esES/patch-esES-Z.MPQ`: unchanged coordinated
  copies from r3, pinned by hashes in the manifest.
- `server/dbc/AreaTrigger.dbc`: staged client-identical DBC, not installed.
- `turtle_wow_crypt_access.sql`: canonical nine-row SQL, identical to project SQL.
- `report.json`: hashes, per-resource MPQ re-extraction roundtrip, original
  resource/row/string preservation, snapshot override probes, DEV collision
  checks, source scan, native display mapping and client/server/SQL dictionaries.

Validated artifact SHA256 values (rebuilds with identical inputs retain these
payload hashes; MPQ container metadata may depend on the packer):

| Output | SHA256 |
|---|---|
| r4.1 T | `0c6e851df5961c0062ba47b617b25078c29b67dacf7278d1b77a259ab031a681` |
| AreaTrigger.dbc | `e28e09f4480662b512801fa9a670b7a42aa28939738376a7081ae2ea1c537aae` |
| Access SQL | `f60861d4aebae154d471de0f1bad8b10bb84d81de218e9554b4829c4dbf6e109` |
| Root Z (unchanged) | `cad32e8e64b89c862b857171fa413557c78e11f04aa2274c2d1af19571a3a022` |
| esES Z (unchanged) | `25708c1a31b5532f111222007861e7bd50aad2beff24b40a27d5331c48958b50` |

DBC output has1222 records/10 fields/40-byte rows. Original1220 row bytes and
the complete string block are preserved exactly, including float bit patterns.
Rows are stably ordered by MapID and the native rows keep their relative order:
the new map0 row is inserted at175, not appended after map724. Build12340
examines a contiguous per-map range and stops at the first larger MapID;
the initial r4 incorrectly appended that row, making entrance900800 invisible
to that scan. The r4 artifact is superseded and must not be installed.
IDs/maps are uint32 and
coordinates/dimensions/orientation are float32. Client and SQL shapes agree to
1e-3 float tolerance. Radius0 uses exact comparison because any positive radius
selects a sphere instead of a box in the core.

The builder probes AreaTrigger by name in every reference335 archive, including
root/locale/custom Z, and coordinated Z copies. Unexpected custom overrides fail
closed; stock locale patch3 must match the pinned baseline. This is a snapshot
audit; the actual playing client's effective patch priority still needs checking.

## SQL review and manual application boundary

Nine rows: two `areatrigger`, two `areatrigger_teleport`, two
`gameobject_template`, two `gameobject`, one `dungeon_access_template`.
Each uses `INSERT ... SELECT constants WHERE NOT EXISTS (all fields match)`.
Identical reruns are no-ops; an occupied key with differing fields produces a
duplicate-key error. Strings are compared byte-exactly, NULLs null-safely and
non-topological floats within1e-3. Related trigger bindings, requirements124,
competing access-map rows and unexpected extra portal spawns also reject setup.

MySQL duplicate-key errors normally roll back only one statement. A short-lived
project-prefixed procedure wraps these nine inserts in a transaction with an
EXIT handler that runs `ROLLBACK; RESIGNAL;`. Success commits and drops the
helper. The account needs CREATE ROUTINE/EXECUTE/ALTER ROUTINE privileges.
Run through a batch client that stops on errors, never `--force`. On a failed
CALL, row changes are rolled back but the helper procedure remains: inspect the
reported collision, then remove `azerothcore_setup_crypt_access` before retrying.
Routine-name collisions fail before any row changes. Run as a standalone SQL
file, not inside another transaction (routine DDL implicitly commits).

After the user's backup/review, the single access file can be applied with:

```sh
mysql --login-path=azeroth-dev --default-character-set=utf8mb4 acore_world < data/sql/custom/db_world/turtle_wow_crypt_access.sql
```

This command is documentation for manual deployment; generation/tests do not
execute it. The nine-row transaction excludes the already-existing instance row.

## DEV deployment and recovery

The main agent subsequently deployed the nine-row SQL in DEV after filtered
backups and independent review. Forward SQL ran twice successfully, all rows
were checked exact, the guarded rollback ran successfully and absence was
confirmed, then forward SQL was reapplied and checked again. The server DBC
was installed and DEV restarted to ready state. Exceptional-handler behavior
has not been fault-injected. Backups and rollback are under
`work/client-overlay-r4/recovery/`.

The builder also generates `rollback_crypt_access.sql` with exact-ownership
and related-dependency guards. On later rebuilds the server DBC may be the
native input, exact old owned r4 output (migration only), or exact corrected
r4.1 output; unrelated drift still fails. Only the corrected stable map order
is emitted in new packages.
A post-deployment rebuild produced the same r4 MPQ. The report.json of a build
describes that builder's read-only actions, not whether an independent DEV
deployment has since occurred. See validation.md for deployment evidence.

After the failed walking test, r4.1 corrected the physical DBC ordering without
changing SQL, IDs, geometry or destinations. The server disk DBC was synchronized
with a backup at `work/client-overlay-r4.1/recovery/AreaTrigger.before.dbc`.
No reload/restart was required for this ordering-only change: this core uses
the already loaded SQL shapes. A seven-test suite now includes the client's
per-map range-selection regression. Walking validation remains pending.

## Validation boundary

Offline tests cover rotated thin-box reachability before the native barrier,
volume edges, conservative no-bounce geometry, ground clearance, quaternion and
phase fields, native Nagrand preservation, uint32 IDs/float32 layout, arbitrary
native float bits/string bytes, malformed/colliding DBCs and manifest/SQL sync.
Archive roundtrips and read-only DEV checks establish artifacts/data only.

SQL forward/idempotency and normal guarded rollback have now been executed as
described above. No source client or core was changed. Manual
validation still needs actual-client DBC priority, non-GM walking before the
wall/gate, visual alignment, arrival floors and facing, no immediate return,
levels54/55, group/solo admission and death/corpse return.
