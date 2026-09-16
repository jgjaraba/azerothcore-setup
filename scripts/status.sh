#!/usr/bin/env bash
#
# Show the status of the AzerothCore DEV authserver and worldserver.
# Validates PID files against /proc/<pid>/exe and cmdline to avoid stale files.
#

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

if ! _acquire_lock 10; then
    exit 1
fi

_any_running=0
_overall_exit=0

# Check using our managed PID file. Removes the file if it is stale.
check_pid_file() {
    local name="$1"
    local pid_file="$2"
    local bin="$3"
    local conf="$4"

    if [[ ! -f "${pid_file}" ]]; then
        return 1
    fi

    local pid
    pid=$(cat "${pid_file}" 2>/dev/null || true)
    if _pid_is_dev_instance "${pid}" "${bin}" "${conf}"; then
        echo "${name}: running (pid ${pid})"
        return 0
    fi

    # PID is missing, reused by another process, or belongs to a different
    # config/binary. Clean up our stale file.
    rm -f "${pid_file}"
    return 1
}

# Fallback: detect any process whose executable + cmdline match this DEV instance.
check_process_fallback() {
    local name="$1"
    local bin="$2"
    local conf="$3"

    local pids
    pids=$(pgrep -f "^${bin}" 2>/dev/null || true)
    if [[ -z "${pids}" ]]; then
        return 1
    fi

    local matches=""
    for pid in ${pids}; do
        if _pid_is_dev_instance "${pid}" "${bin}" "${conf}"; then
            matches="${matches}${pid} "
        fi
    done

    if [[ -n "${matches}" ]]; then
        echo "${name}: running (detected by process scan, pids ${matches% })"
        return 0
    fi

    return 1
}

check_server() {
    local name="$1"
    local pid_file="$2"
    local bin="$3"
    local conf="$4"

    if check_pid_file "${name}" "${pid_file}" "${bin}" "${conf}"; then
        _any_running=1
        return 0
    fi

    if check_process_fallback "${name}" "${bin}" "${conf}"; then
        _any_running=1
        return 0
    fi

    echo "${name}: stopped"
    _overall_exit=1
    return 1
}

echo "AzerothCore DEV server status"
echo "-----------------------------"
check_server "authserver"  "${AUTH_PID_FILE}"  "${AUTH_BIN}"  "${AUTH_CONF}"
check_server "worldserver" "${WORLD_PID_FILE}" "${WORLD_BIN}" "${WORLD_CONF}"

exit "${_overall_exit}"
