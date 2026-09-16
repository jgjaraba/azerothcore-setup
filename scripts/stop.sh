#!/usr/bin/env bash
#
# Stop the AzerothCore DEV authserver and worldserver.
# Only signals processes whose /proc/<pid>/exe matches the exact DEV binaries
# AND whose command line includes the expected DEV config file path.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

_acquire_lock 30

TERM_TIMEOUT_SECONDS=30

stop_by_pid_file() {
    local name="$1"
    local pid_file="$2"
    local bin="$3"
    local conf="$4"

    if [[ ! -f "${pid_file}" ]]; then
        return 1
    fi

    local pid
    pid=$(cat "${pid_file}" 2>/dev/null || true)
    if [[ -z "${pid}" ]] || ! [[ "${pid}" =~ ^[0-9]+$ ]]; then
        rm -f "${pid_file}"
        return 1
    fi

    if ! _pid_is_dev_instance "${pid}" "${bin}" "${conf}"; then
        echo "${name}: stale PID file removed (pid ${pid} does not match this DEV instance)."
        rm -f "${pid_file}"
        return 1
    fi

    echo "${name}: sending SIGTERM to pid ${pid}..."
    kill -TERM "${pid}" 2>/dev/null || true

    local waited=0
    while kill -0 "${pid}" 2>/dev/null && [[ "${waited}" -lt "${TERM_TIMEOUT_SECONDS}" ]]; do
        sleep 1
        ((waited++)) || true
    done

    if kill -0 "${pid}" 2>/dev/null; then
        echo "${name}: pid ${pid} did not terminate in ${TERM_TIMEOUT_SECONDS}s; sending SIGKILL."
        kill -KILL "${pid}" 2>/dev/null || true
        sleep 1
    else
        echo "${name}: stopped."
    fi

    rm -f "${pid_file}"
    return 0
}

# Last-resort fallback scoped by exact binary + config path.
stop_by_process_scan() {
    local name="$1"
    local bin="$2"
    local conf="$3"

    local pids
    pids=$(pgrep -f "^${bin}" 2>/dev/null || true)
    if [[ -z "${pids}" ]]; then
        return 1
    fi

    local stopped_any=0
    for pid in ${pids}; do
        if _pid_is_dev_instance "${pid}" "${bin}" "${conf}"; then
            stopped_any=1
            echo "${name}: stopping orphan DEV process (pid ${pid})."
            kill -TERM "${pid}" 2>/dev/null || true
            local waited=0
            while kill -0 "${pid}" 2>/dev/null && [[ "${waited}" -lt "${TERM_TIMEOUT_SECONDS}" ]]; do
                sleep 1
                ((waited++)) || true
            done
            if kill -0 "${pid}" 2>/dev/null; then
                echo "${name}: SIGKILL orphan pid ${pid}."
                kill -KILL "${pid}" 2>/dev/null || true
            fi
        fi
    done

    return $((1 - stopped_any))
}

stop_server() {
    local name="$1"
    local pid_file="$2"
    local bin="$3"
    local conf="$4"

    local stopped=0
    if stop_by_pid_file "${name}" "${pid_file}" "${bin}" "${conf}"; then
        stopped=1
    fi

    # If no PID file matched, also scan for orphan DEV instances.
    if stop_by_process_scan "${name}" "${bin}" "${conf}"; then
        stopped=1
    fi

    if [[ "${stopped}" -eq 0 ]]; then
        echo "${name}: already stopped."
    fi
}

echo "Stopping AzerothCore DEV servers..."
stop_server "authserver"  "${AUTH_PID_FILE}"  "${AUTH_BIN}"  "${AUTH_CONF}"
stop_server "worldserver" "${WORLD_PID_FILE}" "${WORLD_BIN}" "${WORLD_CONF}"
echo "Done."
