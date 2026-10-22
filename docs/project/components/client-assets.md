# Client assets

The project control repository owns client-facing customization resources:

Client directories supplied for research are snapshots/reference inputs, not
proof of which installation a user is playing. In particular, do not assume
`/home/dev/wow-335` is the active game client or remains synchronized with it.
Establish the provenance of each supplied snapshot and request hashes from the
actual playing installation when diagnosing patch loading. A hash confirms
archive contents, not its effective priority relative to other archives.

### AreaTrigger physical ordering

The inspected build12340 executable scans AreaTrigger.dbc as contiguous
MapID-ordered blocks, stopping at the first larger map. New trigger records
must be inserted by stable MapID order, not simply appended by ID. Preserve
each existing record's bytes and relative order within its map; a record can
be present and valid by ID yet never examined by the client if its physical
position is outside that map's range. The crypt r4 entrance exposed this;
`test_crypt_portals.py` now reproduces the failure and the corrected lookup.

- `dbc/` contains the managed DBC resource set.
- `client_patches/regular_client/patch-Z.mpq` is the regular-client patch.
- `client_patches/hd_client/patch-Z.mpq` is the HD-client patch.
- `client_patches/turtle_crypt/` retains the accepted coordinated esES T/Z set
  separately from an optional stock-esES T and baseline report. Its SHA256SUMS
  and the root README define manual installation/rollback. Server scripts never
  install these MPQs, and the coordinated root Z must not overwrite the HD Z
  without a dedicated merge/audit.
- `addons/` contains the locally distributed Questie and AtlasLoot archives.

The root README directs users to install the patch matching their client. The
NPC creation procedure documents that server DBC files are deployed to
`~/azerothcore/env/dist/bin/dbc` and client DBC files are packaged in an MPQ.

The root README also links DungeonClear, MultiBot-Chatless, and PlayerbotManager
as companion addons, but only Questie and AtlasLoot archives are tracked here.
Their client revisions, installation state, and compatibility with installed
server modules are UNKNOWN. Dungeon Clear and MultiBot Bridge use distinct addon
protocols, so an archive name alone would not prove compatibility.

`scripts/item_dbc_tool.py` is a local utility for safely cloning Item.dbc rows
for custom item IDs; it validates the 3.3.5a WDBC layout and validates its
output after writing. Client patches and DBC files are project-owned assets,
not content maintained in the AzerothCore source checkout.

## Verified SQL contracts

Project custom world SQL requires server/client DBC and patch alignment for the
Dark Rider vendor display `90100` and raid-vendor ExtendedCost records.
`components/custom-world-sql.md` records the database-side requirements and
verification. The audit did not verify that the referenced records are currently
deployed; do not infer that from the SQL alone.

| Feature | Required data contract | Deployment status |
|---|---|---|
| Dark Rider vendors | Display/model `90100` | Unverified server DBC/client patches |
| Raid vendor inventory | Costs in `raid_gear_vendor_item.sql` | Unverified server DBC/client patches |
| Raid/transmog items | Item DBC entries `90001`–`90005` | Present in tracked `dbc/Item.dbc`; deployment unverified |
| Forsaken Paladin trainers | Current template/equipment data | Server/client DBC contract unverified |
| Forsaken Paladin quest items | Item.dbc entries `92060`–`92064` | Present in tracked `dbc/Item.dbc` and required server-side; package into both regular and HD patch-Z archives without discarding existing custom records |
| Orc Mage / Troll Warlock | `CharBaseInfo.dbc` rows `(2, 8)` and `(8, 9)`; `CharStartOutfit.dbc` rows `35`/`36` and `157`/`158` | Present in tracked DBCs and both patch-Z archives; server outfit supplied by `charstartoutfit_dbc` overlay |
| Pending MorphSummon feature | Item DBC entries `91001`–`91079`, if retained | Unverified; not upstream behavior |

Regular and HD patch parity for these contracts has not been inspected.

## Reproducibility boundary

Tracked DBC/MPQ assets prove files are retained in the setup repository, not
their source inputs, build procedure, checksums, deployed server copy, or client
installation. Before changing an item/display/cost/addon contract, record the
server DBC and client artifact relationship and validate the applicable client
variant. See `../CUSTOM-IDENTIFIERS.md` for project identifier evidence.

The Turtle pilot is a scoped exception with explicit final assets/hashes:
server payload/deltas are retained under `data/server/`, and client distributions
under `client_patches/turtle_crypt/`. The [existing-script deployment](../../turtle-wow/deployment.md)
does not require ignored `work/` inputs. This does not certify unrelated client
assets, a complete source rebuild, or new gameplay acceptance of the stock T.

**Observed server-DBC discrepancy (2026-09-20).** The tracked `dbc/Item.dbc`
contains item IDs `90001`–`90005`; the installed server copy contains neither
those IDs nor `91001`–`91079`. Their SHA-256 hashes differ, while matching world
item-template rows were observed. Client MPQ contents and client installation
remain UNKNOWN. Do not treat this as a client parity result or gameplay test.
