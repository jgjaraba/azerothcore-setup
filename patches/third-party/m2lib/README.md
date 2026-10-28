# Pinned M2Lib source and classic-to-Wrath patch

This converter uses **M2Lib by Koward**, with the original project's credits
to Stan84, PhilipTNG, Schlumpf, the Modcraft/WoWDev contributors and testers.
It is a modified build, not an upstream release.

- Original repository: <https://github.com/Koward/M2Lib>
- Exact revision: `18c085632b12e8a19da40df3459f1f4620a30972`
- Original license: **GNU GPL version 2**, verbatim at
  <https://github.com/Koward/M2Lib/blob/18c085632b12e8a19da40df3459f1f4620a30972/LICENSE>
- Original credits:
  <https://github.com/Koward/M2Lib/blob/18c085632b12e8a19da40df3459f1f4620a30972/README.md>
- Project changes: `classic-to-wrath.patch` and
  `tools/new_races_model_converter/{Program.cs,NewRacesModelConverter.csproj}`.
  The driver and patch are distributed under GPL-2.0-only, without warranty.

The build clones that exact source into ignored `work/toolchains/m2lib`, leaving
its original license, author metadata and credits intact. It applies the tracked
patch without a commit. An alternate temporary Git index calculates the expected
patched tree; the working tree must match it exactly. Both an unpatched base and
the exact already-patched tree are supported by the build. Unexpected source
edits, untracked source files and a different HEAD are rejected.

The upstream `LICENSE` is copied alongside the generated DLL. If distributing
the tool, provide the corresponding pinned upstream source, this patch, driver
and build script together with that license. No executable is versioned here.

## Build and validate

Requires Git, Python 3 and an already available **.NET 8 SDK**. The script neither
installs an SDK nor builds AzerothCore. `DOTNET` defaults to `dotnet`; a full SDK
executable path is supported. No `/tmp` path is required by the implementation.

```sh
DOTNET=/path/to/dotnet bash scripts/build-new-races-model-converter.sh
DOTNET=/path/to/dotnet bash scripts/build-new-races-model-converter.sh --validate
```

`--validate` is read-only for the source checkout: it checks the selected SDK,
pinned HEAD, exact patched tree, absence of untracked source, and build manifest
against current driver/project/patch/build-script and output hashes, then runs
the CLI's help command. Run the build first on a clean installation.

Generated assembly:
`work/toolchains/new-races-model-converter/NewRacesModelConverter.dll`.
Intermediate build files are also under `work/toolchains/`.

## Native API and CLI contract

The driver calls M2Lib's `M2.Load(BinaryReader)` and
`M2.Save(BinaryWriter, M2.Format.LichKing)` directly; no legacy executable or
research-only JSON/input manifest is required.

```sh
dotnet work/toolchains/new-races-model-converter/NewRacesModelConverter.dll convert \
  --source 'input/GoblinMale.m2' \
  --output 'work/new-races-models/custom/GoblinMale.m2' \
  --namespace 'Character\Custom\TurtleGoblin\Male' \
  --texture-map 'Character\Goblin\RAG_01.blp=Character\Custom\TurtleGoblin\Male\Textures\RAG_01.blp'
```

`--source`, `--output`, and `--namespace` are required. Output is a **fresh M2
file path**, with adjacent `BASENAME00.skin` (and additional views if present)
and `OUTPUT.m2.report.json`. Existing output files are refused. The source is
read-only. The CLI writes the same report to stdout; errors go to stderr and
return nonzero. The namespace must be below `Character\Custom\`.

Repeat `--texture-map OLD=NEW` for explicit type-0 filename rewrites. Without a
map, each type-0 filename becomes `NAMESPACE\Textures\BASENAME`. Targets must
remain inside the namespace; basename collisions require explicit distinct
maps. Unused maps are errors. Goblin `RAG_01.blp` and `RAG_02.blp` are actual
type-0 resources. Non-null type-8 names, including the supplied BloodElf eye
glow strings, are **not hardcoded texture dependencies**: they remain unchanged
and must not be passed as type-0 maps. An actual type-0 eye glow in another input
is handled by the same generic mapping API. The report's `hardcodedResources`
is the authoritative source-to-target list for the parent asset builder to
copy; the converter does not extract or copy textures.

The report includes `sourceSha256`, the upstream pin, counts, per-file `sha256`
and byte sizes, fallback transformations, unresolved semantic issues, and
`nativeRuntime: "NOT RUN"`. It excludes host paths and timestamps, so reports
are deterministic for identical bytes, output basenames, options and tool.
`fullySupported` refers only to the identified static semantic issues; the
entire artifact remains an experimental stage requiring manual client tests.

## Source preservation and fixes

The patch, dated 2026-10-23 in modified source files:

1. Rebases classic absolute animation/event timestamps to each clip's local
   time without changing global-sequence timestamps. Singleton value tracks are
   constant across the classic timeline and are copied at local timestamp zero
   into every clip, even when their original timestamp lies outside all clips.
   This preserves, for example, the used BloodElf-female opacity of about 0.6.
2. Keeps global tracks in the M2, independent of sequence flags, and stops
   replacing per-sequence track arrays using an inappropriate alias shortcut.
3. Retains the sign bit when packing quaternion components; fixes an ambiguous
   byte conversion overload for .NET 8.
4. Exposes preservation of the source key-bone, texture-replacement, attachment
   and camera lookup arrays, including sentinel/trailing entries which upstream
   otherwise regenerated differently. The driver enables it.

The driver keeps every original clip and its order, geometry, bone identities,
parent/pivot data, and material/skin lookup data. All classic animation payloads
remain embedded (`Stored` is set; no `.anim` files). The first 32 bytes of every
skin section remain intact; the new Wrath bounding center and enclosing radius
are computed from its source vertices. Classic flipbooks and ribbons are explicitly
rejected. Particle conversion has a field-validated support boundary and an
independent native OracleTree control; see [particle layouts and semantics](particles.md).

Wrath removed the classic per-model playable lookup. For every absent action
in that source lookup, the driver materializes per-model sequence records and
tracks from the original fallback clips, preserving variation probabilities
and remapping variation chains. Flags 0 copy the clip; 1 reverses local times
and key order; 3 creates a held terminal pose with a one-millisecond constant
track and no one-shot events. This includes source fallbacks such as
`112 -> 111`, `172/174 -> 16`, `6 -> 1`, and `188/189 -> 50` where absent.
No global AnimationData edit or native/NPC animation substitution is involved.
Runtime state transitions, blending and held/reversed animation behavior still
need manual client verification.

The Goblin interpolation-2 helper tracks are repaired by an **explicit source-hash
and value-hash allowlist** in the driver: male bone **80 Scale**, male bone
**126 Translation**, female bone **90 Scale**. Their source arrays contain one
vector per timestamp, not Wrath's value/in/out spline triples. These three tracks
are changed from interpolation **2 to linear 1**, retaining all timestamp and
key-value bytes (and the existing singleton/local-time conversion). No guessed
tangents or skeleton changes are introduced. This is a bounded helper-curve
approximation, not a claim of source-exact interpolation.

Full ancestry auditing establishes that all three are leaf bones, outside the
weighted-bone parent closure, but **not unused**: male 80 and female 90 drive
attachment ID/index **19**; male 126 drives attachment ID/index **11**. No event,
light, key-bone or key-bone-lookup roots depend on them. Both source cameras are
model-space with no bone binding; ribbons and particles are empty. Thus dropping
or replacing these helpers with identity transforms would be unjustified.

The CLI/report schema remains version 1. Additive `trackRepairs` records include
source/target interpolation, complete source SHA, source timestamp/value hashes,
reasons, direct children/descendants, the full weighted ancestry closure, and
all attachment/event/light/key-bone dependent roots. `unsupportedSemantics`
now identifies bounded **helper-source-curve-approximation**, rather than an
unsafe retained payload; Goblins remain `fullySupported: false`. Attachment
motion and source helper curvature require manual preview; the stage remains
**unaccepted / native runtime NOT RUN**.

Before and after fallback materialization the driver rejects every other
nonempty spline track unless it is a native triple-coefficient camera type:
36-byte position/target keys (three vectors) or 12-byte roll keys (three floats).
It checks logical timestamp/value row and key counts. Unknown source hashes
cannot inherit the helper repair. Reports expose `splineLayoutValidation`;
the four actual models have **zero nonempty spline tracks** after repair.
Spline reverse/freeze semantic ambiguity is still reported if encountered.

## Independent integration checks

```sh
DOTNET=/path/to/dotnet python3 tools/test_new_races_models.py \
  --source-root work/turtle-skins-audit-verified/turtle/resources \
  --output work/new-races-models/validation
```

Requires the four extracted source files, identified by the source character
models for Turtle race 9 Goblin and race 10 BloodElf: Goblin male/female and
BloodElf male/female. The latter outputs are named HighElf; separate
`HighElf*.m2` sources are not used. Model conversion does not allocate race IDs;
the parent new-race stage retains its 22/23 strategy, without NPC replacement.

The independent Python parser checks byte-exact vertices, bind bones, palettes,
source clips/metadata, non-quaternion keys, local/global times, bounds,
materials/lookups, all skins, resources and fallback transformations. Quaternion
component error must be at most `1/32767`. It converts all four models twice,
requires identical M2/skin/report bytes, checks file hashes, absence of `.anim`
files and fresh-output refusal. `validation.json` records measured results and
the per-model irreducible issues. Additional checks independently reconstruct
the complete bone reference audit, check that only the allowlisted interpolation
headers changed, verify every remaining spline key contains three coefficients,
and reject an altered source identity before emitting an unsafe model. A derived
camera fixture exercises nonempty interpolation-2/3 vector and scalar spline
triples because the actual four source models have empty camera spline tracks.
This is static validation, not an in-game test.
