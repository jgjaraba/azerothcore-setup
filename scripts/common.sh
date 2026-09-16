#!/usr/bin/env bash
# shellcheck disable=SC2034
#
# Common variables and helpers for AzerothCore DEV runtime scripts.
#

AC_DIST="/home/dev/azerothcore/env/dist"
CONF_DIR="${AC_DIST}/etc"
LOGS_DIR="${AC_DIST}/logs"
RUN_DIR="${AC_DIST}/run"
LOCK_FILE="${RUN_DIR}/.runtime.lock"

AUTH_BIN="${AC_DIST}/bin/authserver"
WORLD_BIN="${AC_DIST}/bin/worldserver"

AUTH_CONF="${CONF_DIR}/authserver.conf"
WORLD_CONF="${CONF_DIR}/worldserver.conf"

AUTH_PID_FILE="${RUN_DIR}/authserver.pid"
WORLD_PID_FILE="${RUN_DIR}/worldserver.pid"

AUTH_LOG_OUT="${LOGS_DIR}/authserver.out"
WORLD_LOG_OUT="${LOGS_DIR}/worldserver.out"

STARTUP_HEALTH_POLL_SECONDS=10

ensure_dirs() {
    mkdir -p "${LOGS_DIR}" "${RUN_DIR}"
}

# Acquire an exclusive lock to serialize start/stop/status operations.
# Usage: _acquire_lock [timeout_seconds]
_acquire_lock() {
    local timeout="${1:-5}"
    ensure_dirs
    exec 200>"${LOCK_FILE}"
    if ! flock -w "${timeout}" 200; then
        echo "ERROR: another runtime operation is in progress." >&2
        return 1
    fi
}

# Idempotently set a configuration option in an AzerothCore .conf file.
# If the option already exists (commented or uncommented), replace its value.
# Otherwise append it to the end of the file.
_set_config_option() {
    local file="$1"
    local option="$2"
    local value="$3"

    if [[ ! -f "${file}" ]]; then
        echo "ERROR: config file not found: ${file}" >&2
        return 1
    fi

    # Normalize option spacing in existing active lines and commented lines.
    # Replace any active or commented "Option = ..." line with active option.
    if grep -qE "^[[:space:]]*#?[[:space:]]*${option}[[:space:]]*=.*$" "${file}"; then
        sed -i -E "s|^[[:space:]]*#?[[:space:]]*${option}[[:space:]]*=.*$|${option} = \"${value}\"|" "${file}"
    else
        echo "" >> "${file}"
        echo "# Added by azerothcore-setup runtime configuration" >> "${file}"
        echo "${option} = \"${value}\"" >> "${file}"
    fi
}

# Ensure runtime config files point to stable directories. Must be called while
# holding the runtime lock.
ensure_runtime_config() {
    ensure_dirs

    # Back up original configs once so the user can always restore them.
    if [[ ! -f "${AUTH_CONF}.bak" ]]; then
        cp "${AUTH_CONF}" "${AUTH_CONF}.bak"
    fi

    if [[ ! -f "${WORLD_CONF}.bak" ]]; then
        cp "${WORLD_CONF}" "${WORLD_CONF}.bak"
    fi

    _set_config_option "${AUTH_CONF}" "LogsDir" "${LOGS_DIR}"
    _set_config_option "${WORLD_CONF}" "LogsDir" "${LOGS_DIR}"
}

# Return 0 if a process with the given PID is alive.
_pid_is_alive() {
    local pid="$1"
    [[ -n "${pid}" ]] && [[ "${pid}" =~ ^[0-9]+$ ]] && kill -0 "${pid}" 2>/dev/null
}

# Return 0 if a process with the given PID is the expected binary.
_pid_matches_bin() {
    local pid="$1"
    local expected_bin="$2"

    if ! _pid_is_alive "${pid}"; then
        return 1
    fi

    local exe_path
    exe_path=$(readlink -f "/proc/${pid}/exe" 2>/dev/null || true)
    if [[ "${exe_path}" != "${expected_bin}" ]]; then
        return 1
    fi

    return 0
}

# Return 0 if the process was started with the expected config file.
# Parses /proc/<pid>/cmdline as NUL-separated arguments and requires an exact
# `-c <expected_conf>` pair.
_pid_uses_config() {
    local pid="$1"
    local expected_conf="$2"

    if ! _pid_is_alive "${pid}"; then
        return 1
    fi

    local cmdline_file="/proc/${pid}/cmdline"
    if [[ ! -r "${cmdline_file}" ]]; then
        return 1
    fi

    local args=()
    local arg
    while IFS= read -r -d '' arg || [[ -n "${arg}" ]]; do
        args+=("${arg}")
    done < "${cmdline_file}"

    local i
    for ((i = 0; i < ${#args[@]} - 1; i++)); do
        if [[ "${args[$i]}" == "-c" ]] && [[ "${args[$((i + 1))]}" == "${expected_conf}" ]]; then
            return 0
        fi
    done

    return 1
}

# Return 0 only if the PID belongs to this exact DEV instance (binary + config).
_pid_is_dev_instance() {
    local pid="$1"
    local expected_bin="$2"
    local expected_conf="$3"

    _pid_matches_bin "${pid}" "${expected_bin}" && _pid_uses_config "${pid}" "${expected_conf}"
}

# Print a single-line status for a server.
print_process_status() {
    local name="$1"
    local pid="$2"
    local bin="$3"

    if _pid_matches_bin "${pid}" "${bin}"; then
        echo "${name}: running (pid ${pid})"
        return 0
    else
        echo "${name}: stopped"
        return 1
    fi
}
