#!/usr/bin/env bash

set -euo pipefail

CORE="${AZEROTHCORE_ROOT:-$HOME/azerothcore}"
SETUP="${AZEROTHCORE_SETUP_ROOT:-$HOME/azerothcore-setup}"

SRC="$SETUP/harness/opencode"
DEST="$CORE/.opencode"

failures=0

ok() {
    printf 'OK:   %s\n' "$*"
}

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    failures=$((failures + 1))
}

echo "=== AzerothCore OpenCode harness validation ==="
echo

# -------------------------------------------------------------------
# Repository roots
# -------------------------------------------------------------------

git -C "$CORE" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    && ok "AzerothCore Git repository" \
    || fail "AzerothCore is not a Git repository"

git -C "$SETUP" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    && ok "azerothcore-setup Git repository" \
    || fail "azerothcore-setup is not a Git repository"

# -------------------------------------------------------------------
# Shell scripts
# -------------------------------------------------------------------

for script in \
    "$SETUP/scripts/agent/refresh-environment.sh" \
    "$SETUP/scripts/agent/install-harness.sh" \
    "$SETUP/scripts/agent/validate-harness.sh"
do
    if [[ ! -f "$script" ]]; then
        fail "missing script: $script"
        continue
    fi

    if bash -n "$script"; then
        ok "shell syntax: $(basename "$script")"
    else
        fail "shell syntax: $(basename "$script")"
    fi
done

# -------------------------------------------------------------------
# Canonical configuration
# -------------------------------------------------------------------

if python3 -m json.tool "$SRC/opencode.jsonc" >/dev/null 2>&1; then
    ok "canonical opencode.jsonc syntax"
else
    fail "canonical opencode.jsonc syntax"
fi

# -------------------------------------------------------------------
# Required canonical files
# -------------------------------------------------------------------

required_agents=(
    ac-build
    ac-research
    ac-architecture
    ac-review
)

required_commands=(
    start-task
    resume-task
    checkpoint
    verify
    finish-task
)

for agent in "${required_agents[@]}"; do
    [[ -f "$SRC/agents/$agent.md" ]] \
        && ok "canonical agent: $agent" \
        || fail "missing canonical agent: $agent"
done

for command in "${required_commands[@]}"; do
    [[ -f "$SRC/commands/$command.md" ]] \
        && ok "canonical command: $command" \
        || fail "missing canonical command: $command"
done

[[ -f "$SRC/project-instructions.md" ]] \
    && ok "canonical project instructions" \
    || fail "missing canonical project instructions"

# -------------------------------------------------------------------
# No model pinning
# -------------------------------------------------------------------

if grep -Rqs '^model:' "$SRC/agents"; then
    fail "one or more project agents pin a model"
else
    ok "agents are model-independent"
fi

# -------------------------------------------------------------------
# Installed copies
# -------------------------------------------------------------------

compare_file() {
    local source="$1"
    local installed="$2"
    local label="$3"

    if [[ ! -f "$installed" ]]; then
        fail "missing installed file: $label"
        return
    fi

    if cmp -s "$source" "$installed"; then
        ok "installed copy matches canonical: $label"
    else
        fail "installed copy differs from canonical: $label"
    fi
}

compare_file \
    "$SRC/opencode.jsonc" \
    "$CORE/opencode.jsonc" \
    "opencode.jsonc"

compare_file \
    "$SRC/project-instructions.md" \
    "$DEST/project-instructions.md" \
    "project-instructions.md"

for agent in "${required_agents[@]}"; do
    compare_file \
        "$SRC/agents/$agent.md" \
        "$DEST/agents/$agent.md" \
        "agent/$agent"
done

for command in "${required_commands[@]}"; do
    compare_file \
        "$SRC/commands/$command.md" \
        "$DEST/commands/$command.md" \
        "command/$command"
done

# -------------------------------------------------------------------
# Managed marker
# -------------------------------------------------------------------

[[ -f "$DEST/.azerothcore-setup-managed" ]] \
    && ok "managed-install marker" \
    || fail "managed-install marker missing"

# -------------------------------------------------------------------
# Git exclusions
# -------------------------------------------------------------------

exclude="$(git -C "$CORE" rev-parse --git-path info/exclude)"

if [[ "$exclude" != /* ]]; then
    exclude="$CORE/$exclude"
fi

for pattern in '/opencode.jsonc' '/.opencode/'; do
    if grep -qxF "$pattern" "$exclude"; then
        ok "local Git exclude: $pattern"
    else
        fail "missing local Git exclude: $pattern"
    fi
done

# -------------------------------------------------------------------
# OpenCode resolved configuration
# -------------------------------------------------------------------

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

if (
    cd "$CORE"
    opencode debug config > "$tmp"
); then
    ok "OpenCode resolved configuration"
else
    fail "opencode debug config failed"
fi

python3 - "$tmp" <<'PY' || failures=$((failures + 1))
import json
import sys

path = sys.argv[1]

try:
    with open(path) as f:
        cfg = json.load(f)
except Exception as exc:
    print(f"FAIL: cannot parse resolved OpenCode config: {exc}")
    raise SystemExit(1)

failed = False

def check(condition, message):
    global failed
    if condition:
        print(f"OK:   {message}")
    else:
        print(f"FAIL: {message}")
        failed = True

check(
    cfg.get("default_agent") == "ac-build",
    "resolved default_agent is ac-build",
)

agents = cfg.get("agent", {})

expected = {
    "ac-build": "primary",
    "ac-research": "subagent",
    "ac-architecture": "subagent",
    "ac-review": "subagent",
}

for name, mode in expected.items():
    agent = agents.get(name)

    check(
        isinstance(agent, dict),
        f"resolved agent exists: {name}",
    )

    if isinstance(agent, dict):
        check(
            agent.get("mode") == mode,
            f"{name} mode is {mode}",
        )

raise SystemExit(1 if failed else 0)
PY

# -------------------------------------------------------------------
# Model policy
# -------------------------------------------------------------------

MODEL_POLICY="$SRC/model-profiles.env"
PROFILE_LAUNCHER="$SETUP/scripts/agent/opencode-profile.sh"

[[ -f "$MODEL_POLICY" ]] \
    && ok "model policy exists" \
    || fail "model policy missing"

[[ -f "$PROFILE_LAUNCHER" ]] \
    && ok "model profile launcher exists" \
    || fail "model profile launcher missing"

if [[ -f "$PROFILE_LAUNCHER" ]]; then
    if bash -n "$PROFILE_LAUNCHER"; then
        ok "shell syntax: opencode-profile.sh"
    else
        fail "shell syntax: opencode-profile.sh"
    fi
fi

if [[ -f "$MODEL_POLICY" ]]; then
    # shellcheck disable=SC1090
    source "$MODEL_POLICY"

    required_model_vars=(
        AC_GO_BUILD
        AC_GO_RESEARCH
        AC_GO_ARCHITECTURE
        AC_GO_REVIEW
        AC_OPENAI_BUILD
        AC_OPENAI_RESEARCH
        AC_OPENAI_ARCHITECTURE
        AC_OPENAI_REVIEW
    )

    for variable in "${required_model_vars[@]}"; do
        if [[ -n "${!variable:-}" ]]; then
            ok "model policy variable: $variable"
        else
            fail "missing model policy variable: $variable"
        fi
    done
fi

# -------------------------------------------------------------------
# Working-tree information
# -------------------------------------------------------------------

echo
echo "=== Working trees ==="

git -C "$CORE" status --short --branch

echo
git -C "$SETUP" status --short --branch

echo
if [[ "$failures" -eq 0 ]]; then
    echo "HARNESS VALIDATION PASSED"
    exit 0
else
    echo "HARNESS VALIDATION FAILED: $failures check(s)"
    exit 1
fi
