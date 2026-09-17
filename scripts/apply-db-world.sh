#!/usr/bin/env bash

set -euo pipefail

SQL_DIR="/home/dev/azerothcore-setup/data/sql/custom/db_world"
DATABASE="acore_world"
LOGIN_PATH="azeroth-dev"

if [[ ! -d "$SQL_DIR" ]]; then
    echo "ERROR: SQL directory does not exist:"
    echo "  $SQL_DIR"
    exit 1
fi

mapfile -d '' SQL_FILES < <(
    find "$SQL_DIR" \
        -type f \
        -name '*.sql' \
        -print0 |
    sort -z
)

if (( ${#SQL_FILES[@]} == 0 )); then
    echo "No SQL files found in:"
    echo "  $SQL_DIR"
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
