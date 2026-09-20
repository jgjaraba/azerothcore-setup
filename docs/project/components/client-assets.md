# Client assets

The project control repository owns client-facing customization resources:

- `dbc/` contains the managed DBC resource set.
- `client_patches/regular_client/patch-Z.mpq` is the regular-client patch.
- `client_patches/hd_client/patch-Z.mpq` is the HD-client patch.
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
| Pending MorphSummon feature | Item DBC entries `91001`–`91079`, if retained | Unverified; not upstream behavior |

Regular and HD patch parity for these contracts has not been inspected.

## Reproducibility boundary

Tracked DBC/MPQ assets prove files are retained in the setup repository, not
their source inputs, build procedure, checksums, deployed server copy, or client
installation. Before changing an item/display/cost/addon contract, record the
server DBC and client artifact relationship and validate the applicable client
variant. See `../CUSTOM-IDENTIFIERS.md` for project identifier evidence.

**Observed server-DBC discrepancy (2026-09-20).** The tracked `dbc/Item.dbc`
contains item IDs `90001`–`90005`; the installed server copy contains neither
those IDs nor `91001`–`91079`. Their SHA-256 hashes differ, while matching world
item-template rows were observed. Client MPQ contents and client installation
remain UNKNOWN. Do not treat this as a client parity result or gameplay test.
