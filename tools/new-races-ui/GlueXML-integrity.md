# Pinned GlueXML content-integrity gate

## Conclusion and scope

**STATICALLY VERIFIED:** source SHA256
`bf644876709c591acc17c0da8cdf1814edcc9f1e6bc109a8c0d5c38c79dc953c`
does enforce GlueXML content integrity. The cache-only `cf11…` derivative leaves
that gate intact. Changing CharacterCreate/GlueParent while keeping the TOC
unchanged changes the recursively computed content digest and is rejected.

The opt-in **`--allow-custom-gluexml`** profile permits local GlueXML content
modifications by accepting validator status2 (content digest mismatch) at the
GlueXML caller only. It retains cryptographic verification of the existing
native TOC signature, rejects missing/corrupt signatures, and retains the
second digest check for changes between validation and loading. It changes no
shared verifier function, FrameXML validation, account authentication, Warden,
network protections, server logic or licensing checks.

**Windows startup and actual modified-GlueXML load: NOT RUN.** No Wine/Xvfb
runtime test is claimed. This evidence resolves the identified static gate;
it does not certify all native race-dependent paths or model previews.

## Native trace (actual pinned x86)

Addresses below are virtual addresses. `.text` file offsets equal VA−0x400C00.
The relevant names are reconstructed from dataflow/strings, not debug symbols.

1. **GlueXML call site 0x4DA7C2–0x4DA7EA.** The caller initializes an MD5
   context at `[ebp−0xAC]`, supplies an output digest at `[ebp−0x54]`, and
   unconditionally calls0x8165E0 with `Interface\GlueXML\GlueXML.toc`, null
   secondary file, and a public-key pointer. There is no unlocked-client flag
   around this call or switch. The error branches converge on0x4DA81E, which
   invokes the failure path and returns without loading the TOC.
2. **Validator 0x8165E0–0x816766.** Formats `%s.sig` using the TOC filename,
   reads it via0x424E80, returns0 when absent, and requires size0x114 (=276).
   Bad size returns1. The valid-size path lowercases the basename and calls
   signature verification0x816550; failure returns1. That verifier processes
   the signature buffer and basename with the caller's key and calls0x770DB0.
   The latter checks `NGIS` magic, performs its public-key comparison and
   returns the comparison result. Neither function is replaced with a stub.
3. **Content graph hash 0x8166BE–0x816766.** After successful signature
   verification, the validator copies the signature's first16 bytes to a
   local expected-digest buffer, then calls0x8164D0 with the TOC and caller's
   output buffer. It compares the fresh16-byte result with the signed digest.
   Equality returns3; mismatch returns2. In particular, the fresh digest is
   initialized and populated on **both** status2 and status3 paths.
4. **The digest is not TOC-only.** 0x8164D0 initializes MD5 using0x779340
   (standard MD5 IV), calls0x8162B0 for the TOC, and finalizes via0x779AE0.
   0x8162B0 reads each resource, hashes its raw bytes through0x779A30, then
   dispatches `.toc` to0x816060 and `.xml` to0x816240. The TOC walker skips
   comment lines and recursively calls0x8162B0 for named members. The XML
   walker calls0x8160D0, which recognizes `Script`/`Include` and `file` and
   recursively hashes those resources. Thus Lua/XML referenced from an
   unchanged TOC is covered. Raw resource bytes are hashed before parsing.
5. **Return-code switch at0x4DA7E5.** `cmp eax,3; ja failure`, then indirect
   jump through the four dwords at0x4DA9B4. The original table is:

   | Return | Original target | Meaning |
   |---:|---:|---|
   | 0 | 0x4DA7F1 | Missing signature → diagnostic → failure |
   | 1 | 0x4DA7FE | Corrupt/invalid signature → diagnostic → failure |
   | 2 | 0x4DA80B | Modified/corrupt content digest → diagnostic → failure |
   | 3 | 0x4DA835 | Load GlueXML |

6. **Load path 0x4DA835 onward.** Calls0x812B90, then0x814340 with the TOC
   and the already initialized MD5 context at `[ebp−0xAC]`. The loader hashes
   TOC bytes and recursively loads members through0x813EE0; Lua resources use
   0x818F60, XML resources use0x812530 and recursive include/script handling.
   The same MD5-update routine0x779A30 is used. 0x779AE0 finalizes the loaded
   graph digest into `[ebp−0x44]`. 0x4DA863–0x4DA8F1 compares that with the
   verifier's **fresh** digest `[ebp−0x54]`; unequal digests branch back to
   failure at0x4DA81E. This check is left intact. No uninitialized digest is
   consumed when redirecting status2, and the call/stack setup is unchanged.
7. **FrameXML has a separate caller.** Its validator call at0x52ABD1 uses
   the same verifier but a distinct switch at0x52ABDE / table0x52AEB4. The
   opt-in patch edits only the GlueXML table, leaving this path unchanged.

## Reference archive observations

Extracted read-only from the reference enUS archives:

| Member | Archive | Size / SHA256 |
|---|---|---|
| `Interface\GlueXML\GlueXML.toc` | patch-enUS-2.MPQ | 732 / `a0d46e898e5d986c925c93cff09cba11005a8908c6f971c1c5739e9524603413` |
| `Interface\GlueXML\GlueXML.toc.sig` | patch-enUS-3.MPQ | 276 / `0ce72cf65f67d65476fee9d58f97ac033798853f9bf4b2a0de8377bee5483678` |

The inspected TOC lists `GlueParent.xml` and `CharacterCreate.xml`; the latter's
script entry loads CharacterCreate.lua. The generated payload uses that native
graph, appending its custom declarations into existing CharacterCreate.lua,
without requiring a changed TOC or fabricated signature. Signature-file
presence/size is an observation, not a claim that its cryptographic verification
was executed in a running client. Original MPQs must retain the native signature.

## Exact opt-in recipe

The authoritative recipe and precondition bytes are tracked in
`patches/client/new-races-cache.json:custom_gluexml_profile`.

First reproduce and verify the complete cache-only derivative from the pinned
original. Then apply these **cache-relative** edits:

| File offset | Old | New | Reason |
|---:|---|---|---|
| 0xD9DBC | `0B A8 4D 00` | `35 A8 4D 00` | GlueXML status2 target:0x4DA80B→0x4DA835 |
| 0x168 | `5C A5 75 00` | `86 A5 75 00` | PE checksum0x75A55C→0x75A586 |

Only **two bytes** actually differ from the cache-only image:0xD9DBC and0x168.
No instruction length, stack adjustment, call argument, digest buffer, section
attribute or other code is changed. All original cache edits remain present.

Combined derivative SHA256:

```text
87ceca9ea08da2f0d9d312d833ae76751a3ab8f2b8a7d742bfd2356e55f291f3
```

Both modes accept only the original `bf64…` input; unknown/already-patched
inputs are rejected. Source/client-directory output protections still apply.

## Reproduction and tests

The tracked JSON records exact guard bytes for the validator call, bounded
switch/table, signature-size check, cryptographic-verifier branch, graph-digest
output, return-code arithmetic, load call, post-load mismatch branch and separate
FrameXML call. Every guard is checked against the original before generation.
The complete source hash binds the rest of the static trace.

Offline disassembly can be reproduced with the research inspector
`work/new-races-client-research/inspect_client.py dump ADDRESS SIZE` (temporary
pefile/Capstone dependencies), or an ordinary i386 PE disassembler. Production
patching requires no disassembler or third-party Python package.

```sh
python3 tools/patch_new_races_client.py --allow-custom-gluexml \
  --output out/Wow-new-races-custom-gluexml.exe
NEW_RACES_LUA=/tmp/opencode/lua-5.1.5/src/lua \
NEW_RACES_UNICORN_PATH=/tmp/opencode/pydeps \
  python3 tools/test_new_races_client.py
```

Tests cover the original eight cache/UI regressions plus the combined endpoint,
only-allowed byte differences, exact default/custom target tables, unchanged
verifier/load/FrameXML regions, profile guard rejection, repeat-input refusal,
file/report generation and checksum. Optional Unicorn executes the **actual x86
dispatch and post-load comparison blocks** from both images: return codes0/1
still select the original errors;2 changes to load only in the opt-in image;3
loads in both; out-of-range values fail; a post-load digest mismatch still fails.
These block tests are not a Windows process startup or an MPQ-loader execution.
