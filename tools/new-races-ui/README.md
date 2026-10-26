# Additive races: private client utilities

This component stages **22 = TurtleHighElf / Alliance** and
**23 = TurtleGoblin / Horde** for the native 3.3.5 client. It owns the executable
recipe, GlueXML transform and offline tests. DBC/model resources and coordinated
MPQ packaging are delivered by the parent integration.

## Build and output contract

From the setup repository:

```sh
python3 tools/patch_new_races_client.py --allow-custom-gluexml --output out/Wow-new-races-custom-gluexml.exe
python3 tools/build_new_races_glue.py --output work/new-races-glue
NEW_RACES_LUA=/path/to/lua5.1 python3 tools/test_new_races_client.py
```

Both builders require fresh output paths and refuse overwrites. The executable
builder defaults to the pinned `/home/dev/wow-335/Wow.exe`; optional
`--input PATH --output PATH` supports a separately supplied copy of exactly that
input. Output cannot be the input, inside either original reference client, or
inside the supplied executable's directory. Resolving symlinks is part of these
checks. The executable builder uses Python's standard library only.

Executable outputs:

- `out/Wow-new-races-custom-gluexml.exe`
- `out/Wow-new-races-custom-gluexml.report.json`

**Use `--allow-custom-gluexml` for the new-race UI.** The default cache-only
profile remains available for reproducing the original cache proposal, but
retains strict native GlueXML digest checks and rejects this changed XML/Lua
graph. The opt-in profile permits a local GlueXML content digest mismatch only
after the existing TOC signature verifies. Missing/invalid signatures still
fail. Its exact control-flow proof is in [GlueXML-integrity.md](GlueXML-integrity.md).

Glue builder output:

```text
work/new-races-glue/
  report.json
  payload/Interface/GlueXML/CharacterCreate.lua
  payload/Interface/GlueXML/CharacterCreate.xml
  payload/Interface/GlueXML/GlueParent.lua
  payload/Interface/Custom/NewRaces/RaceIcons.blp
```

The additional texture is **included** in the generated payload; no other custom
UI texture is needed. It is the pinned Turtle atlas, used with coordinates parsed
from Turtle's Lua for BloodElf/HighElf and Goblin, both sexes. It is not installed
over the native atlas. Stock picker textures retain `UI-CharacterCreate-Races`;
stock shared portraits retain `UI-CharacterCreate-RacesRound`.

The parent packager can import `tools/build_new_races_glue.py` with `tools` on
`sys.path`, then call `build(output: Path, ...)` to get the report, or
`transform(native_bytes_by_filename, turtle_bytes_by_filename)` to get
`(payload_relative_paths_to_bytes, custom_uv_table)`. These functions enforce the
same source pins. Copy/merge the four payload paths into the parent's coordinated
root/locale Z assembly beside its additive DBC/model resources. No MPQ priority
or successful effective loading is implied by generating these files.

Default extraction uses the project's existing read-only `tools/mpq` CLI
(StormLib; build procedure in `tools/mpq.cpp`/existing project tooling). No SDK or
new Python package is required. Baselines are:

- Native `CharacterCreate.lua` and `.xml`: explicitly
  `/home/dev/wow-335/Data/enUS/patch-enUS-2.MPQ`, pinned member hashes.
- Native `GlueParent.lua`: highest present member among the enumerated native
  enUS patch3, patch2, patch1 and locale candidates. The current winner is
  **patch-enUS-3.MPQ**, SHA256
  `503d2363655a4b3145332a4024ee24240a0ab04b87724b6a6b0ec97fd75d8d31`.
  Its native disconnect/realm fixes are preserved. This is baseline selection,
  not a runtime priority claim about custom Z/M/N archives.
- Turtle `CharacterCreate.lua` and race atlas: explicitly
  `/home/dev/wow-turtle/Data/patch-9.mpq`. The atlas SHA256 is
  `ac9fcae5b16d096d5308ad528fe7427f464cee0df89e7d7d1cd9d407a754d6f7`.

For explicit archive selection, use `--glueparent-archive PATH` and
`--turtle-archive PATH`. For already extracted inputs use
`--source-dir DIR` containing `CharacterCreate.lua`, `CharacterCreate.xml`,
`GlueParent.lua`, and `--turtle-dir DIR` containing `CharacterCreate.lua` and
`RaceIcons.blp`. Explicit inputs disable candidate resolution for those sources;
all member hashes must still match the reviewed pins. All native/Turtle source
pins are in `build_new_races_glue.py` and recorded in the output report.

## Native API and data integration

The native race API returns flat **localized name / fileString / enabled**
triples. The original dynamic enumeration, expansion/account availability and
native class-validity calls are retained. No Lua list manufactures playable
races or classes. Twelve actual XML buttons use picker IDs 1..12, two columns
of six, within the original viewport; all ten native class buttons are retained.
The expected physical-DBC/faction-group enumeration is:

```text
picker ordinal: 1 2 3 4  5  6 7 8 9 10 11 12
actual race ID: 1 3 4 7 11 22 2 5 6  8 10 23
```

`SetSelectedRace(6)` selects High Elf; `SetSelectedRace(12)` selects Goblin.
Race IDs22/23 are never passed as picker ordinals. Actual runtime enumeration
must still be observed with the parent's DBCs. The parent must preserve its
72 existing CharBaseInfo rows (including project custom combinations such as
Undead Paladin), append its 11 new pairs to reach83, and supply full native
customization/model resource closure. NPC Goblin9 and BloodElf10 stay native.

The stable new ChrRaces fileStrings are **TurtleHighElf** and **TurtleGoblin**.
Localized names come from DBCs. The extension declares concise English/Spanish
descriptions and account-disabled messages; it makes no unimplemented racial
ability claims. `NewRaces.lua` is versioned source appended into the generated
native `CharacterCreate.lua`, so the native TOC/XML need no extra script entry.

Temporary preview scene aliases in GlueParent map High Elf to native BloodElf
and Goblin to native Orc. Model path, lighting, fog, ambience and native camera0
all follow that alias; character viewport and other native scenes are preserved.
This reversible visual staging choice does not assign starting zones or change
DBC factions. Goblin framing/scale and both-sex model rendering require actual
client observation; no speculative camera/scale modification is included.

## Executable recipe

Authoritative tracked recipe: `patches/client/new-races-cache.json`. Its fifteen
byte edits and zero append match the researched proposal exactly. Source:

```text
bf644876709c591acc17c0da8cdf1814edcc9f1e6bc109a8c0d5c38c79dc953c
```

The cache formerly at VA0xB6B0D0 would overwrite live selected/facing globals for
race22/23. The builder relocates all eight references to a new fixed-address
RW **non-executable** `.nraces` section at RVA0x9FD000 / VA0xDFD000. It holds
24*2*4 =0xC0 bytes /48 pointers; raw size0x200. Initialization clears0xC0 and
cleanup visits24 races. NumberOfSections, initialized data size, image size,
section header and checksum are updated. Every old-base occurrence must match
the eight proposal offsets. Existing sections and every byte outside allowed
edits remain unchanged. Both input and derivative hashes are hard-pinned, PE
headers are reparsed, and the checksum is independently recomputed.

Expected derivative:

```text
cf11d2794fc4a568f80150f2bf57a3d076d6e79e33b563e26075388477d60c2a
```

That endpoint is the **cache-only** profile. With `--allow-custom-gluexml`, the
derivative SHA256 is:

```text
87ceca9ea08da2f0d9d312d833ae76751a3ab8f2b8a7d742bfd2356e55f291f3
```

It adds one GlueXML jump-table target edit (only one byte actually differs) and
a recalculated PE checksum. Both profiles start from the same original `bf64…`
source, never from an already patched file. The generated Glue payload report
declares the custom-GlueXML profile and its executable hash as requirements.

Unknown and already-patched files are rejected. There is no raceMask hack,
account/server authentication change, or server-side character-creation support.

## Integrity and validation boundary

**Modified-GlueXML acceptance: NOT RUN. Windows startup: NOT RUN. In-client
selection/preview: NOT RUN. This is not a fully working UI acceptance claim.**

Read-only disassembly established an active native validation gate, not merely
diagnostic strings: the validator reads `GlueXML.toc.sig`, checks its signature,
hashes the TOC and recursively referenced XML/Lua, then dispatches return codes
0/1/2 to failure and3 to load. The opt-in profile redirects only status2 to that
existing load path. The validator itself, missing/corrupt-signature handling,
post-load digest consistency check and all FrameXML checks remain byte-exact.
See [the proof and exact byte edits](GlueXML-integrity.md). This is a static
resolution of the content-integrity gate, not an observed client startup.

To establish acceptance, launch a disposable Windows client copy with the
coordinated payload, verify effective GlueXML load/logs, observe36 race values
and correct faction/order, exercise all12 slots, both sexes and every enabled
class, switch stock→22→23→stock repeatedly, randomize and re-enter creation.
Inspect the relocated cache and original neighbouring globals under a debugger.
Keep a valid native `GlueXML.toc.sig` available through the original archives;
do not remove/replace it or distribute a fabricated signature. Any remaining
signature rejection is an unresolved blocker requiring separate hash-pinned
investigation, not a reason to claim this payload worked. A
visible picker never proves unchanged-server creation/login support.

Offline tests verify exact recipe/hash/diff ranges, PE RW/non-executable capacity
and checksum, refusal guards, source preservation, deterministic payloads, real
XML layout/class preservation and stock UV tables. With `NEW_RACES_LUA` they
also execute generated Lua under Lua5.1 using mocked native APIs for both sexes,
English/Spanish text, dynamic triples, enabled state, ordinal clicks, custom and
stock icon switching, class filtering (including Undead Paladin) and scene
lighting/ambience selection. Mocked APIs do not validate the actual native API
or client loader. Without Lua the execution test is explicitly skipped.

Optional `NEW_RACES_UNICORN_PATH=/path/to/temporary/python/dependencies` enables
independent x86 execution of the actual native/patched dispatch and post-load
digest-comparison blocks using Unicorn. Production builders use only stdlib;
Unicorn is a temporary test dependency and is not required for installation.

The executable recipe and UI extension are for private internal client use.
Original client files and Turtle artwork remain subject to their owners' rights;
these utilities grant no redistribution license for those materials.
