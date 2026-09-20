#!/usr/bin/env bash

set -euo pipefail

SQL_DIR="${SQL_DIR:-/home/dev/azerothcore-setup/data/sql/custom/db_world}"
MANIFEST="${MANIFEST:-$SQL_DIR/manifest.txt}"
DATABASE="acore_world"
LOGIN_PATH="azeroth-dev"

usage() {
    echo "Usage: $(basename "$0") [--validate]"
}

validate_manifest() {
    local line
    local line_number=0
    local sql_file
    local discovery_file
    local failures=0
    local -A manifest_lines=()
    local -A manifest_files=()
    local -a discovered_sql_files=()

    if [[ ! -f "$MANIFEST" ]]; then
        echo "ERROR: SQL manifest does not exist:"
        echo "  $MANIFEST"
        return 1
    fi

    if [[ ! -r "$MANIFEST" ]]; then
        echo "ERROR: SQL manifest is not readable:"
        echo "  $MANIFEST"
        return 1
    fi

    while IFS= read -r line || [[ -n "$line" ]]; do
        ((line_number += 1))

        if [[ -z "$line" || "$line" != "${line#"${line%%[![:space:]]*}"}" ||
            "$line" != "${line%"${line##*[![:space:]]}"}" || "$line" == *$'\r'* ||
            "$line" == /* || "$line" == *'/'* || "$line" != *.sql ]]; then
            echo "ERROR: invalid manifest entry on line $line_number: $line"
            failures=1
            continue
        fi

        if [[ -v "manifest_lines[$line]" ]]; then
            echo "ERROR: duplicate manifest entry on lines ${manifest_lines[$line]} and $line_number: $line"
            failures=1
            continue
        fi

        manifest_lines["$line"]=$line_number
        manifest_files["$line"]=1
        SQL_FILES+=("$SQL_DIR/$line")
    done < "$MANIFEST"

    if (( ${#SQL_FILES[@]} == 0 )); then
        echo "ERROR: SQL manifest is empty:"
        echo "  $MANIFEST"
        return 1
    fi

    if ! discovery_file=$(mktemp); then
        echo "ERROR: cannot create temporary file for SQL discovery."
        return 1
    fi

    if ! find "$SQL_DIR" -type f -name '*.sql' -print0 > "$discovery_file"; then
        rm -f "$discovery_file"
        echo "ERROR: cannot discover SQL files in:"
        echo "  $SQL_DIR"
        return 1
    fi

    while IFS= read -r -d '' sql_file; do
        discovered_sql_files+=("$sql_file")
    done < "$discovery_file"

    rm -f "$discovery_file"

    for sql_file in "${SQL_FILES[@]}"; do
        if [[ ! -f "$sql_file" ]]; then
            echo "ERROR: manifest references missing SQL file:"
            echo "  ${sql_file#"$SQL_DIR/"}"
            failures=1
        fi
    done

    for sql_file in "${discovered_sql_files[@]}"; do
        line="${sql_file#"$SQL_DIR/"}"
        if [[ ! -v "manifest_files[$line]" ]]; then
            echo "ERROR: SQL file is not listed in the manifest:"
            echo "  $line"
            failures=1
        fi
    done

    if (( failures != 0 )); then
        return 1
    fi

    return 0
}

if (( $# > 1 )) || { (( $# == 1 )) && [[ "$1" != "--validate" ]]; }; then
    usage
    exit 1
fi

if [[ ! -d "$SQL_DIR" ]]; then
    echo "ERROR: SQL directory does not exist:"
    echo "  $SQL_DIR"
    exit 1
fi

SQL_FILES=()

if ! validate_manifest; then
    echo
    echo "Installation aborted before database access."
    exit 1
fi

if (( $# == 1 )); then
    echo "Manifest validation passed."
    exit 0
fi

echo "============================================================"
echo " AzerothCore custom db_world installer"
echo "============================================================"
echo
echo "Database : $DATABASE"
echo "SQL dir  : $SQL_DIR"
echo "Files    : ${#SQL_FILES[@]}"
echo

for sql_file in "${SQL_FILES[@]}"; do
    relative_path="${sql_file#"$SQL_DIR"/}"

    echo "------------------------------------------------------------"
    echo "Applying: $relative_path"
    echo "------------------------------------------------------------"

    if mysql \
        --login-path="$LOGIN_PATH" \
        --database="$DATABASE" \
        --show-warnings \
        < "$sql_file"
    then
        echo "OK: $relative_path"
    else
        status=$?
        echo
        echo "ERROR applying:"
        echo "  $relative_path"
        echo
        echo "Installation aborted."
        exit "$status"
    fi

    echo
done

echo "============================================================"
echo " All db_world SQL files applied successfully."
echo "============================================================"
