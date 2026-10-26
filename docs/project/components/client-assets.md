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
- [`client_patches/README.md`](../../../client_patches/README.md) owns the current
  installation allowlist and per-patch inventory. Regular uses character-resource
  S, geographic-resource T, nonlocalized-table/interface Z, and localized enUS/esES
  Z. HD is a conservative historical-contract profile with root Z and Spell-only
  locale Z; it does not include the regular customization/new-race/crypt layers.
- Historical regular/HD Z inputs are retained in `client_patches/archive/baselines/`.
  `tools/consolidate_client_patches.py` pins explicit source/member allowlists,
  builds twice, reads back each member and publishes only verified profiles.
  Partial-face alternatives and candidates live under archive and never enter
  that active plan. Required historical inputs are retained under
  `client_patches/archive/source-inputs/`; the canonical source S is
  `archive/source-inputs/Data/patch-S.MPQ`. Logical provenance IDs retain their
  historical names, while the source lock pins their physical archive paths and
  unchanged hashes. Do not remove these inputs with obsolete installation
  packages: they are required for source-based verification/rebuilding. No
  fallback to old active paths or scratch builds is permitted during verification.
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

## Native racial skin customization

The permanent delivery rule is [ADR-0007](../decisions/ADR-0007-native-customization-editions.md):
cumulative principal `client_patches/Data/patch-S.MPQ`, cumulative full optional
alternative `client_patches/archive/optional-extra-skins/Data/patch-S.MPQ`, never loaded
together. Complete ordinary-face banks belong in principal; fixed-face/partial
appearances belong in optional. Prior accepted race data must remain intact.

The [Turtle skin feasibility study](../../turtle-wow/character-skins.md) records
the client/server contract and local resource findings. New native skins use
CharSections body/face/underwear families and the existing Skin Color selector,
not alternate racial displays. Vanilla and Wrath CharSections both have ten
fields but different field order and flag semantics; do not copy them wholesale
or overwrite persisted normal/DK appearance indices.

This AzerothCore checkout leaves appearance-tuple validation as a TODO in
`Player::Create`; it does not implement TrinityCore's `ValidateAppearance`.
Native save/login stores the appearance bytes in the existing character columns.
The supported `charsections_dbc` overlay can represent server-side deltas without
replacing the binary DBC; client textures and CharSections remain necessary.
Playerbots reads the store, so adding face/color rows can affect bot generation.
The [ForestTroll pilot](../../turtle-wow/forest-troll-skins.md) adds six native
colors per sex in a separate patch-S and guarded server SQL. The user confirmed
correct implementation, establishing practical pilot acceptance, not exhaustive
DK/HD or appearance-combination coverage. The broader skin catalog is feasibility evidence,
not a claim that every appearance is implemented or gameplay-validated.

The [frozen Troll bases](../../turtle-wow/troll-customizations.md) retain that
payload, user-confirmed hairstyles and facial features in the **primary** S.
The additional18 appearances are excluded there and kept in a separate optional
full replacement, not an overlay to load beside primary. Seven natural-key
facial-style rows remain common to both clients and server.

The user reported green faces on v2; palette conversion fixed the tested male
pair. All36 retained optional faces use that representation with lossless top
images. The three last male skins33–35 were removed at the user's request,
without investigating their issues; the accepted primary MPQ remains identical.
Full visual acceptance
is not inferred from the one-pair result. Primary has298 server overlays including
Forest; a separate optional SQL manifest adds135 and cleans21 retired legacy
records, not enabled automatically.
Existing characters and other viewers need the edition containing their skins;
the profile switch does not remap stored appearance bytes.

[Tauren](../../turtle-wow/tauren-customizations.md) extends those bases in the
canonical paths with complete five/four-face skins, optional one-face variants,
horn colours/barber unlocks and four new facial keys. Missing geometry is appended
to native M2/SKINs with verified used-bone hierarchies and original animation/
vertex prefixes preserved, not a wholesale Vanilla replacement. Full visual and
animation acceptance is still required, including helmets and other model mods.

For paletted BLP2, alpha is a separate bit plane after palette indices, not the
palette's fourth byte. Pillow13 can misdecode this; use the tested project codec
for these textures, never infer opaque backgrounds and black-key away real art.
Two malformed source terminal mip chains are regenerated with pixel-exact RGBA
top levels and valid native mips, leaving all accepted Forest bytes unchanged.

## Additive new-race client contract

The [High Elf/Goblin client phase](../../turtle-wow/new-races-client.md) allocates
new IDs22/23 rather than replacing playable or NPC races. Canonical S remains
unchanged; this experimental opt-in delivers coordinated derived root/locale-Z
copies to avoid whole-DBC precedence masking. UI uses picker ordinals, not race
IDs; native enumeration is dynamic, but its22-slot appearance cache requires a
hash-guarded executable derivative with a separate RW24-slot cache. Modified
GlueXML also needs the documented local-content acceptance profile; this does
not alter account/network/Warden validation.

The four Turtle models require real256→264 conversion. Source vertices/bind
bones and original animation clips are retained, with per-model fallback
materialization and three explicitly bounded Goblin helper-curve approximations.
Model displays91000–91003 use isolated namespaces. Client bytes/payload closure
are validated. Bounded real regular-client startup and creation-screen rendering
also passed under Wine/Direct3D9 in enUS/esES; server creation/login is not enabled.
Do not
turn a mock/static PASS into gameplay acceptance or deploy client DBCs blindly
to the server; starting data, masks, skills and module compatibility are separate.

### Consolidation: table ownership and HD baseline boundaries

Localized `ChrRaces`, `Map`, `AreaTable`, `MapDifficulty` and `Spell` belong only
to locale Z in the consolidated regular profile. Actual native execution exposed
root copies masking Spanish data; removing the duplicate tables restored names
without changing Glue or the remaining root payload. Do not infer effective
priority from an approximate archive-name sorter or distribute a Spanish table
as an English baseline. In ChrRaces, TeamID column7 is numeric and ClientFileString
column11 is a string offset: a wrong relocation schema can turn `Human` into `an`
and break Glue's scene/ambience selection even when visible names look valid.

The historical HD CreatureDisplayInfo references192 ModelIDs absent from available
stock ModelData, affecting1,734 displays. Its original Z relied on an external HD
table. Preserve that dependency by omitting ModelData replacements, not by copying
the regular full table or inventing aliases. Full HD integration additionally
needs its own appearance/model/animation/texture baseline; retaining HD display
rows alone does not make classic Tauren model replacements HD-compatible.

### CPU character textures are not general GPU textures

The pinned Wrath character compositor requires BLP2 **palette encoding1** for
body input, face/facial overlays, scalps and underwear. General GPU support for
DXT or BGRA does not establish compatibility of those CPU roles. The native
palette accessor at0x4F2D40 rejects other encodings; some composition paths return
without writing, exposing prior-race texture contents, while another fills green.
The new-race fix normalizes only44 affected DXT1 resources and checks role-aware
compatibility. Preserve alpha per mip and disclose RGB quantization. See the
[new-race investigation/fix](../../turtle-wow/new-races-client.md).

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
