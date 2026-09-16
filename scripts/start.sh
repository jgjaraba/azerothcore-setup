#!/usr/bin/env bash
#
# Start the AzerothCore DEV authserver and worldserver.
# Uses stable LogsDir and PID files under env/dist/logs and env/dist/run.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

_acquire_lock 10

# Ensure config points to stable directories while we hold the lock.
ensure_runtime_config

echo "Starting AzerothCore DEV servers..."
echo "  Auth server binary:  ${AUTH_BIN}"
echo "  World server binary: ${WORLD_BIN}"
echo "  Logs directory:      ${LOGS_DIR}"
echo ""

# Track servers started by this invocation so we can roll back on failure.
_STARTED_AUTH=0
_STARTED_WORLD=0

_cleanup_on_failure() {
    echo ""
    echo "ERROR: startup failed. Rolling back servers started by this invocation..." >&2
    if [[ "${_STARTED_AUTH}" -eq 1 ]] && _pid_is_dev_instance "$(cat "${AUTH_PID_FILE}" 2>/dev/null || true)" "${AUTH_BIN}" "${AUTH_CONF}"; then
        local pid
        pid=$(cat "${AUTH_PID_FILE}" 2>/dev/null || true)
        echo "  Stopping authserver (pid ${pid})..." >&2
        kill -TERM "${pid}" 2>/dev/null || true
        sleep 2
        if kill -0 "${pid}" 2>/dev/null; then
            kill -KILL "${pid}" 2>/dev/null || true
        fi
        rm -f "${AUTH_PID_FILE}"
    fi
    if [[ "${_STARTED_WORLD}" -eq 1 ]] && _pid_is_dev_instance "$(cat "${WORLD_PID_FILE}" 2>/dev/null || true)" "${WORLD_BIN}" "${WORLD_CONF}"; then
        local pid
        pid=$(cat "${WORLD_PID_FILE}" 2>/dev/null || true)
        echo "  Stopping worldserver (pid ${pid})..." >&2
        kill -TERM "${pid}" 2>/dev/null || true
        sleep 2
        if kill -0 "${pid}" 2>/dev/null; then
            kill -KILL "${pid}" 2>/dev/null || true
        fi
        rm -f "${WORLD_PID_FILE}"
    fi
    exit 1
}

# Poll a freshly captured PID to confirm the server did not crash immediately.
_wait_for_process() {
    local name="$1"
    local pid="$2"
    local bin="$3"
    local conf="$4"

    local waited=0
    while [[ "${waited}" -lt "${STARTUP_HEALTH_POLL_SECONDS}" ]]; do
        if _pid_is_dev_instance "${pid}" "${bin}" "${conf}"; then
            return 0
        fi
        sleep 1
        ((waited++)) || true
    done

    return 1
}

start_server() {
    local name="$1"
    local bin="$2"
    local conf="$3"
    local pid_file="$4"
    local log_out="$5"
    local started_ref="$6"

    local existing_pid=""
    if [[ -f "${pid_file}" ]]; then
        existing_pid=$(cat "${pid_file}" 2>/dev/null || true)
    fi

    if [[ -n "${existing_pid}" ]] && _pid_is_dev_instance "${existing_pid}" "${bin}" "${conf}"; then
        echo "${name} is already running (pid ${existing_pid}). Skipping."
        return 0
    fi

    if [[ ! -x "${bin}" ]]; then
        echo "ERROR: binary not found or not executable: ${bin}" >&2
        return 1
    fi

    # Remove stale PID file if present.
    rm -f "${pid_file}"

    # Start from AC_DIST so any unexpected relative paths land predictably.
    # Use nohup so the process survives session logout.
    # Close the inherited lock fd (200) so the background server does not hold
    # the runtime lock after this script exits.
    (
        exec 200>&-
        cd "${AC_DIST}"
        nohup "${bin}" -c "${conf}" >> "${log_out}" 2>&1 &
        echo $! > "${pid_file}"
    )

    local pid
    pid=$(cat "${pid_file}" 2>/dev/null || true)

    if _wait_for_process "${name}" "${pid}" "${bin}" "${conf}"; then
        eval "${started_ref}=1"
        echo "${name} started (pid ${pid}). Console output: ${log_out}"
    else
        echo "ERROR: ${name} failed to start. Check ${log_out}" >&2
        return 1
    fi
}

# Trap ERR so a failure in either start_server rolls back only what we started.
trap '_cleanup_on_failure' ERR

start_server "authserver"  "${AUTH_BIN}"  "${AUTH_CONF}"  "${AUTH_PID_FILE}"  "${AUTH_LOG_OUT}"  "_STARTED_AUTH"

# Give authserver a moment to bind port 3724 before starting worldserver.
sleep 2

start_server "worldserver" "${WORLD_BIN}" "${WORLD_CONF}" "${WORLD_PID_FILE}" "${WORLD_LOG_OUT}" "_STARTED_WORLD"

trap - ERR

echo ""
echo "Use '${SCRIPT_DIR}/status.sh' to check readiness."
echo "Use '${SCRIPT_DIR}/stop.sh'  to stop the servers."
