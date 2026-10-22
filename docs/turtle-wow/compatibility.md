# Turtle WoW maps — compatibility

Curated reference for migrating custom geography from Turtle's Vanilla 1.12.1
build 5875 snapshot to WotLK 3.3.5a build 12340. Findings from individual samples
are scoped evidence, not a guarantee for every Turtle map or modified continent
tile. The long-term scope includes all custom geography; gameplay imports are
outside this geographic procedure.

## Formats and evidence boundaries

| Resource | Established facts | Migration requirement / remaining uncertainty |
|---|---|---|
| MPQ | `MPQ\x1A` is a signature, not a format-version declaration. Measured Turtle patch9 and 335 patch-Z headers are 32 bytes / `wFormatVersion=0`; measured 335 common-2 and patch-enUS-3 headers are 44 bytes / version 1. | Inspect each archive's header and effective load priority; do not assign one format version to an entire client. StormLib can read these samples. |
| ADT framing | Both sampled clients use MVER 18 and 0x80-byte MCNK headers. Sampled area IDs are at MCNK magic +0x3C (payload +0x34); MCIN entries use absolute MCNK offsets. | Matching MVER does not establish identical flags, alpha encoding, optional chunks or liquid behavior. Validate offsets, sizes and chunk identities independently. |
| Terrain / alpha | Sampled MCVT/MCNR/MCLY/MCAL/MCRF/MCSH framing can be retained for the dry pilot. One matched `kalimdor_28_40` pair has byte-identical MCLY entries. | This does not prove all payloads interchangeable. Interpret alpha using WDT flags, MCLY flags and actual MCAL encoding; do not force a conversion solely because MVER is 18. |
| WDT | Both inspected samples contain MVER, MPHD and MAIN (64×64 entries of 8 bytes). The compared 335 sample also has an empty MWMO placeholder. Neither sample establishes an MPH2 layout. | Check flags and any global WMO references. For shared continents merge only justified MAIN changes while preserving native tile availability and unrelated data. |
| ADT liquids | Vanilla stores MCLQ per MCNK; WotLK supports file-level MH2O. The native map extractor reads both (`src/tools/map_extractor/adt.h` and `System.cpp` in the core root). | Server extraction support does not prove client rendering. No project MCLQ→MH2O converter is implemented. Wet-map viability needs explicit format, liquid-type, mask, height and client/server checks. |
| Optional chunks | MFBO describes flight bounds. Its absence in a sample is not a universal incompatibility. | Do not call MFBO a performance optimization, or assume MCSE is WotLK-only/absent in Vanilla. Inventory optional chunks per input before preserving, translating or omitting them. |
| DBC | Observed Map schemas: Turtle 42 fields / 335 66; AreaTable: Turtle 25 / 335 **36**. | Translate fields and locale strings explicitly; never copy whole Turtle tables over destination DBCs. See [ID mappings](id-mappings.md). |
| M2 / WMO / BLP | Some paths resolve to native 335 assets; Vanilla MMDX names often use `.mdx` where 335 uses `.m2`. | Path existence is only reference resolution. Check version, geometry, collision, groups, materials, animations and liquid semantics as applicable. BLP encoding and mip descriptors need inspection, not blanket conversion. |

### Known parser/serializer limitation before wet maps

The correct zero-based MHDR field order after MODF (index 8) is:

| MHDR index | Chunk |
|---|---|
| 9 | MFBO |
| 10 | MH2O |
| 11 | MTXF |

**Current `tools/adt_convert.py` and `tools/adt.py` misinterpret these indices.**
The converter lists MH2O at 9, MTXF at 10 and MFBO at 12; the parser labels index
9 as MH2O. This is a latent defect not exercised by the dry pilot ADTs. Before
processing wet or optional-chunk-bearing maps, correct and independently verify
the parser/serializer against native layouts and real fixtures. No such code fix
is part of this documentation update. The old reference to
`mclq_to_mh2o.py` was removed from the converter's docstring; that converter
does not exist.

The earlier recipes naming MCNK `HasBigAlpha=0x100` and `HasMh2o=0x1000` are
withdrawn. Those names/bits are **not verified operational instructions**.
Establish the correct flag owner, bit meaning and applicable format before
changing flags, clearing MCLQ offsets, or changing alpha/liquid payloads.

## Asset fidelity and the accepted pilot

The actual pilot is **KarazhanCrypt, map 800: six ADTs and one WDT**. Balor
(source map 818, nine ADTs + WDT in the earlier candidate set) was considered
and discarded as the pilot; it is not the demonstrated conversion chain.

Identical WMO paths did not preserve Turtle behavior. Native
`MD_Crypt_D_000.wmo` contains an invisible collision box absent from Turtle.
Both complete crypt families are WMO v17 with 19 groups, but their group order
differs. The tower `kharazan.wmo` also differs (11 Turtle groups vs 12 native).
Never mix roots and numbered groups from different families or equate pathname
existence with fidelity.

The working adaptation uses a complete native crypt family at
`World\wmo\Custom\Turtle800\tw800crypt.wmo`, with only the demonstrated extra
barrier removed. Both path **and basename** are isolated because the VMap
extractor flattens filenames. It does not globally override the Blizzard WMO,
and is not a complete Turtle WMO conversion. Crypt WMO MLIQ water in five groups
is separate from ADT MCLQ/MH2O; the user's water checks do not validate an ADT
water converter.

Other reusable pilot lessons:

- Shortening MMDX names requires rebuilding MMID byte offsets while preserving
  placement/slot identity. Likewise validate MWMO/MWID and MODF indirections.
  Enumerating valid path strings alone missed the original client defect.
- Interior minimaps must match group identity and bounds, not array position.
  The pilot uses 18 Turtle interior images and five native-image aliases where
  bounds differ, plus six Turtle exterior minimap tiles.
- World-map labels are baked into artwork. DBC translations cannot repaint
  them; preserve the user-approved manual Spanish artwork as an input.
- Inspect BLP mip ranges. The loading-screen adaptation normalizes only stale
  inactive descriptors, preserving active image bytes; it is not an artwork
  conversion or a universal BLP1→BLP2 requirement.

The user confirmed exploration, cartography, loading screen, walking access,
temporary-rabbit movement and the agreed short wall/between-floor/water-edge
checks. This closes the **practical geographic pilot**. Six terrain, VMap and
MMap tiles are recorded as generated; the offline navigation suite still has
410 partial/disconnected combinations. Neither all room connections nor all
Turtle geography is certified. See [validation](validation.md) and
[navigation](navigation.md) for evidence and limits.

## Reusable procedure for future geographic migrations

This is the required scope of investigation and validation, not a claim that
the current pilot-specific scripts implement a generic all-map pipeline.

1. **Establish effective inputs.** Identify source snapshot, reference client,
   actual playing client, locale, archive hashes and loose-file overrides.
   Resolve each resource's provenance. `tools/mpq_priority.py` uses an assumed
   static order and cached listings; verify it against actual client selection.
   Extractors forcing T last do not prove the game client selects T.
2. **Classify the geographic delta.** Separate independent maps, additions on
   shared continents and modifications of existing tiles. Enumerate common as
   well as source-only ADTs, WDT availability, neighboring seams, WDL/minimap
   resources and dependencies. The 175 source-only tiles are not an inventory
   of all modified geography; see [inventory](maps-inventory.md).
3. **Resolve identifiers and semantics.** Check client DBCs, server DBCs, SQL
   overlays and project allocations independently. Record source→destination
   mappings for every affected namespace; retain native records and strings.
   MapDifficulty 754 was hidden by server SQL, and AreaTrigger records require
   stable MapID ordering for the observed client lookup. Presence by ID alone
   does not prove a usable record.
4. **Choose adaptation per resource.** Preserve verified-compatible data;
   translate references and indirections; investigate alpha/liquids/optional
   chunks with real samples. Close the MHDR defect before wet-map processing.
   Resolve transitive WMO/M2/BLP dependencies and document any fidelity loss.
   Reference libraries such as `warcraft-rs`/`wow-adt` can inform research; they
   are not an implemented project converter or a substitute for validation.
5. **Merge additively.** Independent-map packaging must still handle occupied
   Map IDs. Shared-continent work must preserve unrelated native ADTs and WDT
   entries, reconcile modified common tiles and check boundaries. A WMA bounding
   rectangle is not an exact ADT merge selection. Merge cartography, locale
   metadata, loading screens and native access only as the region requires.
6. **Build a reproducible package.** Record tool/library requirements, source
   hashes, all indispensable inputs, transformations and expected outputs.
   Present project source (`tools/crypt_portals.json`, builders and SQL) carries
   technical decisions; extracted `work/` reports are local evidence, not a
   versioned source-of-truth manifest. Inspect tracking/input availability
   before claiming recovery from a clean clone. The current r1–r5 chain also
   consumes preceding packages and the manual PNG; it is not a generic bootstrap.
7. **Check effective packaging and server data.** Round-trip all MPQ resources;
   verify unrelated bytes and actual root/locale precedence. Stage DBC,
   Maps/VMaps/MMaps from the coordinated client with matching extractors.
   Check missing dependencies, expected tile coverage and generator diagnostics
   even on exit 0. Record extractor source/build prerequisites explicitly.
8. **Validate within stated bounds.** Test structural correctness separately
   from client rendering, terrain seams, liquid behavior, collision, navigation,
   access and native-map regressions. Retain installation/rollback instructions
   for the coordinated archive/server set and distinguish user-confirmed
   gameplay from offline diagnostics. Close a region only to its demonstrated
   acceptance scope; do not infer global completeness from one pilot.

Tel'Abim supplies a real wet-ADT subset for a future viability study, but neither
its complete perimeter nor a safe continental merge is established. The missing
WMO acquisition and measured subset are recorded in the inventory. Detailed
scheduling belongs in the roadmap; compatibility requirements belong here.
