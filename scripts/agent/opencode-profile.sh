#!/usr/bin/env bash

set -euo pipefail

SETUP="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
POLICY="$SETUP/scripts/agent/model-profiles.env"

[[ -f "$POLICY" ]] || {
    echo "ERROR: model profile file not found: $POLICY" >&2
    exit 1
}

# shellcheck disable=SC1090
source "$POLICY"

profile="${1:-go}"

case "$profile" in
    go)
        BUILD="$AC_GO_BUILD"
        RESEARCH="$AC_GO_RESEARCH"
        REVIEW="$AC_GO_REVIEW"
        ;;
    openai|fallback)
        BUILD="$AC_OPENAI_BUILD"
        RESEARCH="$AC_OPENAI_RESEARCH"
        REVIEW="$AC_OPENAI_REVIEW"
        ;;
    status)
        printf 'OpenCode Go\n-----------\nac-build:    %s\nac-research: %s\nac-review:   %s\n\n' \
            "$AC_GO_BUILD" "$AC_GO_RESEARCH" "$AC_GO_REVIEW"
        printf 'OpenAI fallback\n---------------\nac-build:    %s\nac-research: %s\nac-review:   %s\n' \
            "$AC_OPENAI_BUILD" "$AC_OPENAI_RESEARCH" "$AC_OPENAI_REVIEW"
        exit 0
        ;;
    *)
        echo "Usage: $0 [go|openai|status]" >&2
        exit 2
        ;;
esac

export OPENCODE_CONFIG_CONTENT="$(python3 - "$BUILD" "$RESEARCH" "$REVIEW" <<'PY'
import json
import sys

build, research, review = sys.argv[1:]
print(json.dumps({"agent": {
    "ac-build": {"model": build},
    "ac-research": {"model": research},
    "ac-review": {"model": review},
}}))
PY
)"

cd "$SETUP"
exec opencode --agent ac-build
