# High Elf Map0 — durable regular-client source

This directory is a build input, never an installation profile. `source-lock.json` pins every payload, independent baseline, delta, expected full result and upstream evidence manifest by SHA-256/size. Its own SHA-256 is pinned in `tools/package_high_elf_map.py`.

The hook reconstructs the historical consolidation first, verifies all original regular delivery hashes without modifying the old source lock, then applies only the listed edits. Full DBCs are rebuilt from staged independent baselines plus relocatable deltas and compared against the pinned result hashes. Diffs are in each DBC edit. Native record and string-block prefixes remain byte-exact. `work/` paths in evidence are provenance only; the normal hook never opens them.

Ownership: shared geography (including isolated Character/Custom/HighElfMap models) in T without DBC; AreaTable and WMOAreaTable in both locale Z; WorldMapArea and WorldMapOverlay in root Z. S and all unrelated members and HD remain byte-exact. The complete TRS retains crypt/native mappings outside its explicit regional update list.

Build from repository root with TMPDIR="$PWD/work/tmp":

```sh
work/new-races-image-venv/bin/python tools/consolidate_client_patches.py --output work/high-elf-map-rebuild --reproducible
work/new-races-image-venv/bin/python tools/consolidate_client_patches.py --verify client_patches
```

Export TMPDIR for both commands. To reconstruct the exact old delivery use `--native-only --output work/high-elf-map-rollback --reproducible`; verify it with `--native-only --verify work/high-elf-map-rollback`. Publication remains the consolidator transactional `--publish` operation. Manual installation/rollback is described in client_patches/README.md. No snapshots or server files are installed by this hook.

An explicit source migration may use `--baseline-source DIRECTORY --baseline-source-sha256 HISTORICAL_LOCK_SHA256` during capture. This historical pin is separate from the current active-source pin. Only independently pinned baseline files are recovered; integrated result tables are never accepted as a new pre-map baseline.
