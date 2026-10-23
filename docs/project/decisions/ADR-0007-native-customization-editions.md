# ADR-0007: Cumulative native customization editions by compatibility

Status: Accepted
Date: 2026-10-23

## Context

Turtle appearance resources include full racial component families, fixed-face
bakes, geometry and legacy placeholders. Enabling them all as ordinary skin
colours hides real limitations. The user explicitly chose a persistent split
for Tauren and every subsequent racial customization migration.

## Decision

- `client_patches/Data/patch-S.MPQ` is the cumulative **primary** edition. New
  skins must have every ordinary native face variation supported by actual
  authored components, not aliases of one bake disguised as several faces.
- `client_patches/optional-extra-skins/Data/patch-S.MPQ` is a cumulative **full
  alternative**, including primary plus fixed-face or other partially compatible
  appearance choices. It is not an overlay; never load both editions.
- Both are manually installed as the single `Data/patch-S.MPQ`. Retain and pin
  previous accepted race inputs so adding a race cannot silently regress it.
- Class-specific DK coverage, unsupported geometry, missing resources and HD
  compatibility are recorded separately. Data completeness is not visual proof.
  Do not fabricate faces or map unavailable geometry to an unrelated native one.
- Preserve Wrath skeletons/animations and old appearance indices. Where genuinely
  new geometry is needed, append only validated pieces with proven bone binding;
  do not replace a native model wholesale with a Vanilla file.
- Principal metadata belongs to the existing world SQL manifest. Partial options
  are separate opt-in SQL, so default bot generation does not select absent
  principal-client resources. File deltas use the existing server-data hook.
- Never silently remap saved appearances when changing profiles. Optional-look
  characters and their viewers need the edition containing those resources.

## Alternatives considered

### One archive with everything enabled

Rejected: fixed faces would be presented as complete, and the default client
would include partially compatible options the user wants to keep optional.

### A primary archive plus an independently loaded optional overlay

Rejected: whole-table DBC overrides create precedence/dependency problems.
Complete replacement editions make their exact appearance stores verifiable.

### New races, display morphs, or wholesale Vanilla model replacement

Rejected for this scope: native customization should keep race identity, gear,
animations and ordinary persistence, without a separate transformation system.

## Consequences

### Positive

- A stable manual installation path and explicit compatibility contract.
- Per-race preservation checks; predictable default and opt-in server profiles.
- Authored full-face options are distinguishable from baked appearances.

### Negative / trade-offs

- Two full archives must be generated and checked on every migration.
- Clients lacking optional resources cannot faithfully display optional-look
  characters. SQL does not transmit textures or enforce a cosmetic unlock gate.
- Geometry and rendering still require actual client acceptance; structural
  tests cannot certify their appearance.

## References

- [Client asset contract](../components/client-assets.md)
- [Tauren customization](../../turtle-wow/tauren-customizations.md)
- [Troll baseline](../../turtle-wow/troll-customizations.md)
