#!/usr/bin/env bash

set -euo pipefail

SETUP="${AZEROTHCORE_SETUP_ROOT:-$HOME/azerothcore-setup}"
POLICY="$SETUP/harness/opencode/model-profiles.env"

[[ -f "$POLICY" ]] || {
    echo "ERROR: model policy not found: $POLICY" >&2
    exit 1
}

# shellcheck disable=SC1090
source "$POLICY"

profile="${1:-go}"

case "$profile" in
    go)
        BUILD="$AC_GO_BUILD"
        RESEARCH="$AC_GO_RESEARCH"
        ARCHITECTURE="$AC_GO_ARCHITECTURE"
        REVIEW="$AC_GO_REVIEW"
        ;;

    openai|fallback)
        BUILD="$AC_OPENAI_BUILD"
        RESEARCH="$AC_OPENAI_RESEARCH"
        ARCHITECTURE="$AC_OPENAI_ARCHITECTURE"
        REVIEW="$AC_OPENAI_REVIEW"
        ;;

    status)
        cat <<STATUS
OpenCode Go
-----------
ac-build:        $AC_GO_BUILD
ac-research:     $AC_GO_RESEARCH
ac-architecture: $AC_GO_ARCHITECTURE
ac-review:       $AC_GO_REVIEW

OpenAI fallback
---------------
ac-build:        $AC_OPENAI_BUILD
ac-research:     $AC_OPENAI_RESEARCH
ac-architecture: $AC_OPENAI_ARCHITECTURE
ac-review:       $AC_OPENAI_REVIEW
STATUS
        exit 0
        ;;

    *)
        echo "Usage:" >&2
        echo "  $0 go" >&2
        echo "  $0 openai" >&2
        echo "  $0 status" >&2
        exit 2
        ;;
esac

RUNTIME_CONFIG="$(
python3 - \
    "$BUILD" \
    "$RESEARCH" \
    "$ARCHITECTURE" \
    "$REVIEW" <<'PY'
import json
import sys

build, research, architecture, review = sys.argv[1:]

print(json.dumps({
    "agent": {
        "ac-build": {
            "model": build
        },
        "ac-research": {
            "model": research
        },
        "ac-architecture": {
            "model": architecture
        },
        "ac-review": {
            "model": review
        }
    }
}))
PY
)"

export OPENCODE_CONFIG_CONTENT="$RUNTIME_CONFIG"

echo "OpenCode model profile: $profile"
echo "  ac-build:        $BUILD"
echo "  ac-research:     $RESEARCH"
echo "  ac-architecture: $ARCHITECTURE"
echo "  ac-review:       $REVIEW"
echo

cd "$HOME/azerothcore"

exec opencode --agent ac-build
