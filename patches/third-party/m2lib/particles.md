# Classic particle conversion (v256 → v264)

The project driver overrides M2Lib's speculative legacy lifetime/spin mapping.
The pinned upstream source/patch and license remain as documented in `README.md`.
No particles are removed, replaced by geometry or marked supported by an allowlist.
Support is determined from each input's actual fields and track layout.

## Layout and independent evidence

- [WoWDev M2ParticleOld](https://wowdev.wiki/M2#M2ParticleOld) describes the
  pre-Wrath lifetime ramps and the Wrath fake tracks. v256 records are **504**
  bytes at header array **316**; v264 records are **476** bytes at array **296**.
- The real HIGHELTREE source from Turtle `patch-5.mpq` has SHA256
  `60e87d8a3a315dfc69acd043d3f7d8a0da7d3cf1cb78d8d6c4b447fdd0fd2029`.
  Its ten particles have the same IDs, positions, bones, textures and static
  parameters as the native 3.3.5a
  `World\Kalimdor\Kalidar\PassiveDoodads\OracleTree\OracleTree.m2`, from
  `common-2.MPQ` (SHA256
  `f91b13392c7ba56fd2f1f51c0d2cbff40711094fcad898e0d53ca42f8a8001fb`).
  This is a control for particle data, **not** a replacement tree.
- The integration harness independently compares the emitted lifetime tracks,
  complete identity/bindings, low flags plus head/tail style, spin, tail/twinkle,
  follow parameters and tumble/wind with that native control. The native exporter
  produces RGB floats differing from integer bytes by at most `2e-5`; output
  retains the exact integer color components. Alpha, scale, UV times/cells and
  other static numeric values match exactly (including negative spin).

## Field mapping

Offsets below are relative to each record, not the file.

| Classic | Wrath | Meaning |
|---|---|---|
| 0–39 | 0–39 | Identity, flags, position, bone/texture, two filename arrays |
| 40/42: two uint16 | 40/41: two bytes; 42: uint16 zero | Blend/emitter; no classic particle-color replacement index |
| 44–51 | 44–51 | Particle type, head/tail, priority plane and atlas dimensions |
| 52–331: ten 28-byte tracks | 52–259: ten 20-byte tracks plus two new zero variations | Speed, variation, ranges, gravity, life, rate, area axes, z source |
| 332: float midpoint | fake-track fixed0.15 timestamps | `[0, round(midpoint*32767), 32767]` |
| 336: three BGRA colors | 260: RGB float fake track; 276: alpha fixed0.15 fake track | RGB in 0..255; alpha `round(A*32767/255)` (255 must become 32767) |
| 348: three scalar sizes | 292: XY fake track | Both X **and Y** equal the scalar size; zero XY variation |
| 360: two uint16 start/end/repeat triples | 316: head UV fake track | `[start, lifeEnd, decayStart, end]` at `[0,mid,mid,32767]` |
| 372: two int16 start/end pairs | 332: tail UV fake track | Only all-zero tail UVs are accepted, yielding an empty implicit first-cell track |
| 380–407 | 348–375 | Tail length, twinkle, inheritance and drag |
| 408: spin | 384: spin speed | **Not** base rotation; new base spin and variation fields stay zero |
| 412–447 | 396–431 | Tumble min/max and wind vector, preserved component-for-component |
| 448 | 392 | Wind time (M2Lib calls this `Blank2`, but it is not padding) |
| 452–467 | 432–447 | Follow speed/scale pairs |
| 468: spline point array | 448: spline point array | Empty in supported plane/sphere inputs |
| 476: enabled track | 456: enabled track | Boolean keys, not silently coerced arbitrary bytes |

Preserve the low classic flags and explicitly materialize the head style bit
`0x20000`, as in the native control; retain the original head/tail byte as well.
Tail/both styles require another independent control and are rejected. The actual
native control covers low flags `0x1`, `0x20`, `0x21`, `0x220`; other low flags
are preserved verbatim, without a claim of independent runtime coverage.
Do not reinterpret signed spin or priority plane.
The native control establishes direct spin-speed mapping; a lifetime-based spin
rescaling or assigning it to base rotation would change these real emitters.

All eleven ordinary tracks use the existing conversion of absolute sequence times
to clip-local time, global-loop retention, singleton constants and materialized
fallbacks. Lifetime fake tracks are separate, parametrized by each particle's age,
and must **not** be copied/reversed as model animation tracks. Duplicate midpoint
UV keys represent the two one-sided values at the life/decay discontinuity.

## Fail-closed support boundary

Validation occurs before M2Lib loads the particle arrays. It bounds every array,
rejects narrowing of blend/emitter integers, checks bone/texture bindings,
finite scalars, valid midpoint nondegenerate both before and after quantization,
boolean enable values, supported
interpolation/global-loop indexes, paired timestamp/value counts and monotonic
times. Multikey local keys must belong to a source clip, and legacy index ranges,
when provided, must agree with the time-based split. Unsupported inputs fail
before creating a model or skin.

Currently supported: type-0 billboard plane/sphere emitters with scalar instant or
linear tracks, head lifetime ramps, and nonrepeating head UV phases.
Tail/both style, nonzero tail UVs, model/child-emitter filenames, spline generators/points, unknown classic high flag
bits, nonempty spline tracks, repeated head UV phases and range/time disagreement
are rejected, rather than guessing their semantics. Flipbooks and ribbons remain
separately rejected. These boundaries are content checks, not source-hash repairs.

Time and alpha quantization are explicit format changes: nearest fixed0.15 gives
at most `0.5/32767` normalized error. RGB, scalar emission keys, isotropic sizes,
UV cells and static floats are preserved without fitting or approximation.
`fullySupported` means no identified unsupported static conversion semantics;
it does not assert that the candidate has been rendered in a client.

## Reproduce validation

```sh
DOTNET=/path/dotnet scripts/build-new-races-model-converter.sh
DOTNET=/path/dotnet scripts/build-new-races-model-converter.sh --validate
tools/mpq extract-one /home/dev/wow-335/Data/common-2.MPQ \
  'World\Kalimdor\Kalidar\PassiveDoodads\OracleTree\OracleTree.m2' \
  work/FRESH/native-oracle.m2
DOTNET=/path/dotnet python3 tools/test_m2_particles.py \
  --native-oracle work/FRESH/native-oracle.m2 --output work/m2-particles/FRESH
```

Use fresh existing parent directories for extraction. The four real integration
fixtures are source-hash pinned in the harness. It also validates the shared model
geometry/skins/animation contract, two-build determinism and fresh-output refusal.
A derived fixture exercises global linear and singleton tracks, enabled keys,
reverse/frozen fallbacks, head UVs, nonzero tumble/wind/windTime, plus malformed
and unsupported cases which must fail without outputs. Run the original
`test_new_races_models.py` integration separately to retain the four race models'
quaternion, helper-repair, camera-spline and original output contracts.

The build wrapper refreshes `work/toolchains/new-races-model-converter/build-manifest.json`:
it locks the driver/project/patch/build-script and all generated tool files by
SHA256, in addition to the upstream pin and patched tree. `--validate` rejects
stale source or binaries. This update does not require re-freezing source archives
or changing `tools/client-patches-sources.json`.
