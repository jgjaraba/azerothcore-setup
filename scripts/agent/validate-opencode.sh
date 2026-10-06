#!/usr/bin/env bash

set -euo pipefail

SETUP="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CORE="${AZEROTHCORE_ROOT:-$HOME/azerothcore}"
CONFIG="$SETUP/opencode.jsonc"
AGENTS="$SETUP/.opencode/agents"

expected=(ac-build ac-research ac-review)
failures=0

ok() { printf 'OK:   %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; failures=$((failures + 1)); }

echo "=== OpenCode project validation ==="
echo "workspace: $SETUP"

if python3 -m json.tool "$CONFIG" >/dev/null 2>&1; then
    ok "project opencode.jsonc is valid JSON"
else
    fail "project opencode.jsonc is invalid"
fi

[[ -f "$SETUP/AGENTS.md" ]] && ok "project AGENTS.md exists" || fail "project AGENTS.md is missing"
[[ -f "$SETUP/docs/project/README.md" ]] && ok "project knowledge entry point exists" || fail "docs/project/README.md is missing"

agent_count=0
for file in "$AGENTS"/*.md; do
    [[ -e "$file" ]] || continue
    agent_count=$((agent_count + 1))
done
[[ "$agent_count" -eq 3 ]] && ok "exactly three project agent files exist" || fail "found $agent_count project agent files, expected 3"

for agent in "${expected[@]}"; do
    [[ -f "$AGENTS/$agent.md" ]] && ok "project agent exists: $agent" || fail "project agent missing: $agent"
done
[[ ! -e "$AGENTS/ac-architecture.md" ]] && ok "ac-architecture is absent" || fail "ac-architecture remains"

for removed in \
    "$SETUP/harness/opencode" \
    "$SETUP/scripts/agent/install-harness.sh" \
    "$SETUP/scripts/agent/refresh-environment.sh" \
    "$SETUP/plans"
do
    [[ ! -e "$removed" ]] && ok "obsolete path absent: ${removed#"$SETUP"/}" || fail "obsolete path remains: $removed"
done

if [[ -d "$SETUP/.opencode/commands" ]] && compgen -G "$SETUP/.opencode/commands/*.md" >/dev/null; then
    fail "custom command files remain"
else
    ok "no custom task commands remain"
fi

for script in "$SETUP/scripts/agent/validate-opencode.sh" "$SETUP/scripts/agent/opencode-profile.sh"; do
    if bash -n "$script"; then ok "shell syntax: ${script##*/}"; else fail "shell syntax: ${script##*/}"; fi
done

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

if (cd "$SETUP" && opencode debug config) >"$work/config.json" 2>"$work/config.err"; then
    ok "OpenCode discovers the project config from the setup workspace"
else
    fail "opencode debug config failed: $(tail -n 1 "$work/config.err")"
fi

python3 - "$work/config.json" "$CONFIG" "$CORE" "${expected[@]}" <<'PY' || failures=$((failures + 1))
import json
import sys

resolved_path, source_path, core_root, *expected = sys.argv[1:]
failed = False

def check(condition, message):
    global failed
    print(f"{'OK:  ' if condition else 'FAIL:'} {message}")
    failed |= not condition

try:
    with open(resolved_path) as stream:
        resolved = json.load(stream)
    with open(source_path) as stream:
        source = json.load(stream)
except Exception as exc:
    print(f"FAIL: cannot parse OpenCode configuration: {exc}")
    raise SystemExit(1)

check(resolved.get("default_agent") == "ac-build", "default agent is ac-build")
agents = resolved.get("agent", {})
check(set(agents) == set(expected), f"project agents are exactly {expected}: {sorted(agents)}")
for name, mode in (("ac-build", "primary"), ("ac-research", "subagent"), ("ac-review", "subagent")):
    check(isinstance(agents.get(name), dict) and agents[name].get("mode") == mode,
          f"{name} mode is {mode}")
check("ac-architecture" not in agents, "resolved config has no ac-architecture")
commands = resolved.get("command", {}) or {}
check(not commands, f"no custom commands are resolved: {sorted(commands)}")

source_permissions = source.get("permission", {})
external = source_permissions.get("external_directory", {})
check(external.get(core_root + "/**") == "allow", "AzerothCore root is trusted for external access")
check(source_permissions.get("edit") == "allow", "ordinary editing is allowed")
bash = source_permissions.get("bash", {})
check(bash.get("*") == "allow", "ordinary shell execution is allowed")
check(bash.get("git commit*") == "deny", "git commit is denied")
check(bash.get("git push*") == "deny", "git push is denied")

resolved_external = resolved.get("permission", {}).get("external_directory", {}) or {}
check(resolved_external.get(core_root + "/**") == "allow",
      "resolved config allows external AzerothCore access")

raise SystemExit(1 if failed else 0)
PY

for agent in "${expected[@]}"; do
    if (cd "$SETUP" && opencode debug agent "$agent") >"$work/$agent.json" 2>"$work/$agent.err"; then
        ok "opencode debug agent $agent resolves from setup workspace"
        python3 - "$work/$agent.json" "$agent" <<'PY' || failures=$((failures + 1))
import fnmatch
import json
import sys

path, name = sys.argv[1:]
with open(path) as stream:
    agent = json.load(stream)
rules = agent.get("permission", [])

def action(tool, subject):
    result = None
    for rule in rules:
        if rule.get("permission") in (tool, "*") and fnmatch.fnmatchcase(subject, rule.get("pattern", "*")):
            result = rule.get("action")
    return result

checks = {
    "ordinary edit": ("edit", "README.md", "allow"),
    "ordinary shell": ("bash", "ls", "allow"),
    "commit": ("bash", "git commit -m probe", "deny"),
    "push": ("bash", "git push origin main", "deny"),
    "git -C commit": ("bash", "git -C /home/dev/azerothcore commit -m probe", "deny"),
    "git -C push": ("bash", "git -C /home/dev/azerothcore push origin main", "deny"),
}
failed = False
for label, (tool, subject, expected) in checks.items():
    actual = action(tool, subject)
    passed = actual == expected
    print(f"{'OK:  ' if passed else 'FAIL:'} {name}: {label} resolves {actual!r}, expected {expected!r}")
    failed |= not passed
raise SystemExit(1 if failed else 0)
PY
    else
        fail "opencode debug agent $agent failed: $(tail -n 1 "$work/$agent.err")"
    fi
done

stale="$(grep -rIl \
    -e 'ac-architecture.md' \
    -e 'harness/opencode' -e 'install-harness.sh' -e 'managed-install marker' \
    -e 'installed harness' -e 'canonical harness' -e 'canonical vs installed' \
    -e 'refresh-environment' -e 'generated/ENVIRONMENT' \
    -e 'plans/active' -e 'plans/completed' -e 'plans/TEMPLATE' \
    -e 'start-task.md' -e 'resume-task.md' -e 'checkpoint.md' -e 'verify.md' -e 'finish-task.md' \
    "$SETUP/README.md" "$SETUP/AGENTS.md" "$SETUP/docs" "$SETUP/scripts" "$SETUP/opencode.jsonc" "$AGENTS" 2>/dev/null \
    | grep -v 'decisions/ADR-' | grep -v 'scripts/agent/validate-opencode.sh' || true)"
if [[ -n "$stale" ]]; then
    printf '%s\n' "$stale" >&2
    fail "stale references to the removed installation/task model remain"
else
    ok "no stale installation or task-machinery references remain outside ADR history"
fi

echo
if [[ "$failures" -eq 0 ]]; then
    echo "OPENCODE VALIDATION PASSED"
    exit 0
fi
echo "OPENCODE VALIDATION FAILED: $failures check(s)"
exit 1
