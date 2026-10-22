# Pilot extractor support — preserved source patch

`turtle-pilot-extractors.patch` captures only the previously implemented pilot
changes to `src/tools/map_extractor/System.cpp` and
`src/tools/vmap4_extractor/vmapexport.cpp`. Reference baseline:
`a66f1bede6f5d905d9ab815715b4e2ee1c1f48e7` in the local core lineage.
No unrelated Unit/selection modifications are included.

## Contract and limits

- Both tools explicitly open root `Data/patch-T.MPQ` last.
- VMap extractor adds `--only <mapID>` to restrict map placement processing;
  it can still extract global models. It expects `-d` to point to **Data**,
  whereas map_extractor's `-i` points to the **client root**.
- This is the Linux pilot implementation, not a generic client-priority
  resolver. `fopen64` and permissive `atoi` parsing are preserved as-is; use a
  validated decimal Map ID on the tested Linux environment. Cross-platform
  portability and a generalized archive list remain follow-up work.
- Forcing T last does **not** prove the game client loads T over Z. Resolve
  client root/locale overrides before extraction. The pilot's reconciled Z
  copies and independent-client checks are essential.

The patch is preserved for recovery under ADR-0003, not evidence that it is
already in an upstream commit or that the same changes apply to every revision.
The main core README continues to document the unrelated combo-points patch.

## Validate/apply/build

From the setup root:

```sh
scripts/apply-core-patches.sh --validate
```

Only after preserving unrelated work and verifying a compatible core, use the
installer to apply missing patches. On an incompatible revision, resolve the
conflict; do not force it. This documentation update does not change native
source or installed tools: it captures existing changes. A fresh tool build
after applying requires the native build dependencies and appropriate CMake
tool targets:

```sh
cmake --build /home/dev/azerothcore/build --target map_extractor vmap4_extractor -j2
```

Install these rebuilt tools deliberately to the extraction workspace/runtime
tool location; do not imply that a worldserver rebuild is required just for
these tool-source changes. A full build/install is outside this command.

## Remove

On a compatible source tree, after checking unrelated changes:

```sh
git -C /home/dev/azerothcore apply --reverse --check \
  /home/dev/azerothcore-setup/patches/core/turtle-pilot-extractors.patch
git -C /home/dev/azerothcore apply --reverse \
  /home/dev/azerothcore-setup/patches/core/turtle-pilot-extractors.patch
```

Then rebuild the two tools before reusing them. This removes only extractor
support; it does not revert any client or server geographic data. Do not use
the unpatched tools to silently regenerate the custom map without equivalent
archive selection support.
