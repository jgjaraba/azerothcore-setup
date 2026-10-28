# Native ADT client probe

`probe_adt_client.py` executes the client's actual x86 MCNK scanner, with its
legacy-fix argument set to 1, in Unicorn. It does not launch WoW. Inputs remain
read-only; native writes affect only an emulated cell copy. It does not repair
or normalize data before testing.

## Dependencies and use

Use an isolated environment with the pinned requirements:

```sh
python3 -m venv /tmp/opencode/adt-probe-venv
/tmp/opencode/adt-probe-venv/bin/pip install -r tools/probe-adt-client-requirements.txt
/tmp/opencode/adt-probe-venv/bin/python tools/probe_adt_client.py \
  --adt-dir /path/to/World/Maps/Azeroth \
  --exe /path/to/Wow.exe --exe /path/to/Wow-new-races.exe \
  --output /path/to/evidence.json
```

Alternatively, set `PYTHONPATH` to an already installed isolated dependency
directory. The tool has no scratch-directory imports or dependency discovery.

All directly contained `*.adt` files are tested, including every populated MCIN
slot, not just selected source cells. To validate published resources, add
`--mpq /path/to/patch-T.MPQ`. In that mode the ADT directory's filenames define
the scope: those exact `World\Maps\Azeroth\<filename>` members are freshly
extracted to a disposable temporary directory before all their cells are
tested. Existing extracted files are never reused or overwritten. The default
extractor is the adjacent `tools/mpq`; override with `--mpq-tool` if needed.
For the high-elf region, supply its 24-tile directory to test all 6144 cells.
This mode targets Azeroth members, not arbitrary map namespaces or effective
multi-archive client priority.

## Validation contract

- Only x86 PE files at image base `0x400000` are supported. The inclusive
  `0x7c3a10..0x7c3b3b` function must have SHA256
  `c5c8779e6e404d3fa2c62f221ca3e91de4414d3d130f50dea3ed644af88ea5f6`.
  Incompatible code is refused before emulation; hooks depend on those bytes.
- The minimal object, stack and cell buffer are synthesized. Only the pinned
  function bytes are mapped as client code. Each call resets registers and
  scratch memory; MCNK capacity is 65536 bytes. Larger cells are refused.
- Instruction hooks observe actual tag dispatch at `0x7c3a42` and effective
  subchunk sizes at `0x7c3b26`, after native MCNR/MCAL/MCLQ fixups. Unknown tags,
  headers/extents outside the exact MCNK and an inexact final cursor all fail.
  An ordinary return alone is insufficient. Invalid memory accesses, code
  escapes and exhausted instruction budgets also fail. The default budget is
  100000 instructions per call, configurable with `--instruction-limit`.
- Reports include input ADT hashes, full EXE/function hashes, dependency
  versions, observation time, counters and per-cell failures. MPQ mode also
  records the archive hash. Exit codes: **0** all cells pass; **1** completed
  validation with failures (expected for a negative baseline); **2** setup or
  input failure. A setup failure does not produce a new evidence report.

Native probe regression tests (requires the same dependencies):

```sh
ADT_PROBE_EXE=/path/to/Wow.exe /tmp/opencode/adt-probe-venv/bin/python \
  -m unittest discover -s tools -p test_probe_adt_client.py -v
python3 -m unittest discover -s tools -p test_high_elf_terrain.py -v
```

The first suite executes real pinned instructions against synthetic adversarial
cells: an unmapped fault followed by a clean call, a returning unknown-tag
walk, a returning overrun, budget exhaustion and a modified-EXE hash rejection.
Without `ADT_PROBE_EXE` these native contracts explicitly skip. Terrain tests
include snapshot-dependent tests with their own availability checks.

## Interpretation limits

This is an offline, bounded scanner test, not a complete PE loader, client map
load or renderer test. It proves neither water rendering nor subsequent liquid
consumers, GPU behavior, archive priority, gameplay, or the cause of a screenshot
from an executable whose bytes are unavailable. Baseline and corrected data
must be tested separately; old reports are not evidence of a current run.
