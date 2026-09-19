#!/usr/bin/env bash

set -euo pipefail

CORE="${AZEROTHCORE_ROOT:-$HOME/azerothcore}"
SETUP="${AZEROTHCORE_SETUP_ROOT:-$HOME/azerothcore-setup}"

SRC="$SETUP/harness/opencode"
DEST="$CORE/.opencode"
MARKER="$DEST/.azerothcore-setup-managed"

die() {
    echo "ERROR: $*" >&2
    exit 1
}

[[ -d "$CORE" ]] ||
    die "AzerothCore directory not found: $CORE"

git -C "$CORE" rev-parse --is-inside-work-tree >/dev/null 2>&1 ||
    die "Not a Git working tree: $CORE"

for required in \
    "$SRC/opencode.jsonc" \
    "$SRC/project-instructions.md" \
    "$SRC/agents/ac-build.md" \
    "$SRC/agents/ac-research.md" \
    "$SRC/agents/ac-architecture.md" \
    "$SRC/agents/ac-review.md"
do
    [[ -f "$required" ]] ||
        die "Missing canonical harness file: $required"
done

tracked="$(
    git -C "$CORE" ls-files -- \
        opencode.jsonc \
        .opencode
)"

if [[ -n "$tracked" ]]; then
    echo "$tracked" >&2
    die "A managed target is tracked by the AzerothCore repository."
fi

conflict=0

if [[ ! -f "$MARKER" ]]; then
    for path in \
        "$CORE/opencode.jsonc" \
        "$DEST/project-instructions.md" \
        "$DEST/agents" \
        "$DEST/commands" \
        "$DEST/skills"
    do
        if [[ -e "$path" ]]; then
            echo "Existing unmanaged path: $path" >&2
            conflict=1
        fi
    done
fi

[[ "$conflict" -eq 0 ]] ||
    die "Refusing to overwrite an unmanaged local OpenCode configuration."

mkdir -p "$DEST"

rm -rf \
    "$DEST/agents" \
    "$DEST/commands" \
    "$DEST/skills"

rm -f \
    "$DEST/project-instructions.md"

install -m 0644 \
    "$SRC/opencode.jsonc" \
    "$CORE/opencode.jsonc"

install -m 0644 \
    "$SRC/project-instructions.md" \
    "$DEST/project-instructions.md"

cp -a "$SRC/agents" "$DEST/agents"
cp -a "$SRC/commands" "$DEST/commands"

mkdir -p "$DEST/skills"

if [[ -d "$SRC/skills" ]]; then
    cp -a "$SRC/skills/." "$DEST/skills/"
fi

cat > "$MARKER" <<MARKER_EOF
Managed by:
$SETUP/scripts/agent/install-harness.sh

Canonical source:
$SRC
MARKER_EOF

exclude="$(
    git -C "$CORE" rev-parse --git-path info/exclude
)"

if [[ "$exclude" != /* ]]; then
    exclude="$CORE/$exclude"
fi

mkdir -p "$(dirname "$exclude")"
touch "$exclude"

for pattern in \
    '/opencode.jsonc' \
    '/.opencode/'
do
    grep -qxF "$pattern" "$exclude" ||
        echo "$pattern" >> "$exclude"
done

echo "OpenCode harness installed successfully."
echo
echo "Canonical source:"
echo "  $SRC"
echo
echo "Installed into:"
echo "  $CORE/opencode.jsonc"
echo "  $DEST/"
