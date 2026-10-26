#!/usr/bin/env bash
# Rebuild the GPL-2.0 M2Lib-based converter without system installation.
set -euo pipefail
root="$(realpath "$(dirname "${BASH_SOURCE[0]}")/..")"
dotnet="${DOTNET:-dotnet}"
pin=18c085632b12e8a19da40df3459f1f4620a30972
source="$root/work/toolchains/m2lib"
patch="$root/patches/third-party/m2lib/classic-to-wrath.patch"
project="$root/tools/new_races_model_converter/NewRacesModelConverter.csproj"
output="$root/work/toolchains/new-races-model-converter"
mode="${1:-build}"
[[ $# -le 1 && ( "$mode" == build || "$mode" == --validate ) ]] || { printf '%s\n' "Usage: $0 [--validate]" >&2; exit 2; }
command -v "$dotnet" >/dev/null || { printf '%s\n' 'Set DOTNET to a .NET 8 SDK executable (default: dotnet).' >&2; exit 1; }
"$dotnet" --list-sdks | python3 -c 'import sys; assert any(x.startswith("8.") for x in sys.stdin), "A .NET 8 SDK is required"'
[[ "$("$dotnet" --version)" == 8.* ]] || { printf '%s\n' 'DOTNET must select a .NET 8 SDK.' >&2; exit 1; }
test -f "$project" && test -f "$patch"
if [[ ! -d "$source/.git" ]]; then
    [[ "$mode" != --validate ]] || { printf '%s\n' "Missing pinned source: $source; run the build first." >&2; exit 1; }
    mkdir -p "$root/work/toolchains"
    git clone --no-checkout https://github.com/Koward/M2Lib.git "$source"
    git -C "$source" checkout --detach "$pin"
fi
[[ "$(git -C "$source" rev-parse HEAD)" == "$pin" ]] || { printf '%s\n' 'M2Lib source is not at the pinned revision.' >&2; exit 1; }
# Compute the exact expected patched tree without staging or modifying the checkout index.
index="$(mktemp "$root/work/toolchains/m2lib-index.XXXXXX")"
rm "$index"
trap 'rm -f "$index"' EXIT
export GIT_INDEX_FILE="$index"
git -C "$source" read-tree "$pin"
git -C "$source" apply --cached "$patch"
tree="$(git -C "$source" write-tree)"
unset GIT_INDEX_FILE
if git -C "$source" diff --quiet "$pin" --; then
    [[ "$mode" != --validate ]] || { printf '%s\n' 'M2Lib patch has not been applied; run the build first.' >&2; exit 1; }
    git -C "$source" apply --check "$patch"
    git -C "$source" apply "$patch"
fi
git -C "$source" diff --exit-code "$tree" --
[[ -z "$(git -C "$source" ls-files --others -- M2Lib/src)" ]] || { printf '%s\n' 'Untracked M2Lib source files are not allowed.' >&2; exit 1; }
printf 'M2Lib base=%s patched_tree=%s\n' "$pin" "$tree"
# Reject stale builds during --validate; keep all generated state under ignored work/.
check_build() {
    python3 - "$root" "$tree" "$mode" <<'PY'
import hashlib, json, pathlib, sys
root, tree, mode = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
out = root / 'work/toolchains/new-races-model-converter'
paths = ['tools/new_races_model_converter/Program.cs',
         'tools/new_races_model_converter/NewRacesModelConverter.csproj',
         'patches/third-party/m2lib/classic-to-wrath.patch',
         'scripts/build-new-races-model-converter.sh']
paths += [str(p.relative_to(root)) for p in sorted(out.glob('*')) if p.is_file() and p.name != 'build-manifest.json']
assert (out / 'NewRacesModelConverter.dll').is_file(), 'Build the converter first'
manifest = {'patched_tree': tree, 'sha256': {
    p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths}}
path = out / 'build-manifest.json'
if mode == '--validate':
    assert json.loads(path.read_text()) == manifest, 'Stale/modified converter: rebuild first'
else:
    path.write_text(json.dumps(manifest, indent=2) + '\n')
PY
}
if [[ "$mode" == --validate ]]; then
    check_build
    "$dotnet" "$output/NewRacesModelConverter.dll" --help
    exit 0
fi
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
"$dotnet" build "$project" -c Release --output "$output" \
    -p:BaseIntermediateOutputPath="$root/work/toolchains/new-races-model-converter-obj/" \
    -p:M2LibSource="$source" -p:RestoreIgnoreFailedSources=true
check_build
printf 'CLI: %s "%s/NewRacesModelConverter.dll" convert --source INPUT --output FRESH.m2 --namespace "Character\\Custom\\Turtle..."\n' "$dotnet" "$output"
