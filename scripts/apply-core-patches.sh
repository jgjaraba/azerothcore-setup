#!/usr/bin/env bash
#
# Apply core source patches tracked under azerothcore-setup.
#
# Usage:
#   scripts/apply-core-patches.sh [--validate]
#
# --validate performs a dry run and reports whether each patch is applicable,
# already applied, or in conflict, without modifying the working tree.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETUP_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PATCH_DIR="${PATCH_DIR:-${SETUP_ROOT}/patches/core}"
MANIFEST="${MANIFEST:-${PATCH_DIR}/manifest.txt}"
REPO="${REPO:-/home/dev/azerothcore}"

EXPECTED_BASE="${EXPECTED_BASE:-b4bbae96d3ff9fd8b85bede269cfba8ad28aad2a}"

usage() {
  echo "Usage: $(basename "$0") [--validate]"
  echo
  echo "Environment overrides:"
  echo "  PATCH_DIR   directory containing patches and manifest (default: ${PATCH_DIR})"
  echo "  MANIFEST    ordered patch inventory (default: ${MANIFEST})"
  echo "  REPO        target AzerothCore repository (default: ${REPO})"
}

validate_manifest() {
  local line
  local line_number=0
  local patch_file
  local discovery_file
  local failures=0
  local -A manifest_lines=()
  local -A manifest_files=()
  local -a discovered_patch_files=()

  if [[ ! -f "$MANIFEST" ]]; then
    echo "ERROR: patch manifest does not exist:"
    echo "  $MANIFEST"
    return 1
  fi

  if [[ ! -r "$MANIFEST" ]]; then
    echo "ERROR: patch manifest is not readable:"
    echo "  $MANIFEST"
    return 1
  fi

  while IFS= read -r line || [[ -n "$line" ]]; do
    ((line_number += 1))

    if [[ -z "$line" || "$line" == \#* ]]; then
      continue
    fi

    if [[ "$line" != *.patch || "$line" == */* ]]; then
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
    PATCH_FILES+=("${PATCH_DIR}/$line")
  done < "$MANIFEST"

  if (( ${#PATCH_FILES[@]} == 0 )); then
    echo "ERROR: patch manifest is empty:"
    echo "  $MANIFEST"
    return 1
  fi

  if ! discovery_file=$(mktemp); then
    echo "ERROR: cannot create temporary file for patch discovery."
    return 1
  fi

  if ! find "$PATCH_DIR" -maxdepth 1 -type f -name '*.patch' -print0 > "$discovery_file"; then
    rm -f "$discovery_file"
    echo "ERROR: cannot discover patch files in:"
    echo "  $PATCH_DIR"
    return 1
  fi

  while IFS= read -r -d '' patch_file; do
    discovered_patch_files+=("$patch_file")
  done < "$discovery_file"

  rm -f "$discovery_file"

  for patch_file in "${PATCH_FILES[@]}"; do
    if [[ ! -f "$patch_file" ]]; then
      echo "ERROR: manifest references missing patch file:"
      echo "  ${patch_file#"${PATCH_DIR}/"}"
      failures=1
    fi
  done

  for patch_file in "${discovered_patch_files[@]}"; do
    line="${patch_file#"${PATCH_DIR}/"}"
    if [[ ! -v "manifest_files[$line]" ]]; then
      echo "ERROR: patch file is not listed in the manifest:"
      echo "  $line"
      failures=1
    fi
  done

  if (( failures != 0 )); then
    return 1
  fi

  return 0
}

check_repo() {
  if [[ ! -d "${REPO}/.git" ]]; then
    echo "ERROR: target repository is not a git checkout: ${REPO}"
    return 1
  fi

  local current_head
  current_head=$(git -C "$REPO" rev-parse HEAD)

  if [[ "$current_head" != "$EXPECTED_BASE" ]]; then
    echo "WARNING: repository HEAD ${current_head} differs from the patch base ${EXPECTED_BASE}."
    echo "         Patches may not apply cleanly; review conflicts carefully."
  fi
}

patch_state() {
  local patch_file="$1"

  if git -C "$REPO" apply --check --reverse "$patch_file" >/dev/null 2>&1; then
    echo "already-applied"
    return 0
  fi

  if git -C "$REPO" apply --check "$patch_file" >/dev/null 2>&1; then
    echo "applicable"
    return 0
  fi

  echo "conflict"
  return 0
}

apply_patch() {
  local patch_file="$1"
  local relative
  relative="${patch_file#"${PATCH_DIR}/"}"
  local state

  state=$(patch_state "$patch_file")

  case "$state" in
    already-applied)
      echo "SKIP (already applied): $relative"
      return 0
      ;;
    applicable)
      echo "Applying: $relative"
      if git -C "$REPO" apply "$patch_file"; then
        echo "OK: $relative"
        return 0
      else
        echo "ERROR: failed to apply: $relative"
        return 1
      fi
      ;;
    conflict)
      echo "ERROR: patch conflicts with current tree: $relative"
      echo "       Run 'git -C ${REPO} apply --check ${patch_file}' for details."
      return 1
      ;;
  esac
}

if (( $# > 1 )) || { (( $# == 1 )) && [[ "$1" != "--validate" ]]; }; then
  usage
  exit 1
fi

if [[ ! -d "$PATCH_DIR" ]]; then
  echo "ERROR: patch directory does not exist:"
  echo "  $PATCH_DIR"
  exit 1
fi

PATCH_FILES=()

if ! validate_manifest; then
  echo
  echo "Validation aborted before repository access."
  exit 1
fi

check_repo

if (( $# == 1 )) && [[ "$1" == "--validate" ]]; then
  echo "Patch dry-run validation:"
  echo
  validate_failures=0
  for patch_file in "${PATCH_FILES[@]}"; do
    validate_relative="${patch_file#"${PATCH_DIR}/"}"
    validate_state=$(patch_state "$patch_file")
    case "$validate_state" in
      already-applied) echo "  ALREADY APPLIED : $validate_relative" ;;
      applicable)      echo "  APPLIES CLEANLY : $validate_relative" ;;
      conflict)        echo "  CONFLICT        : $validate_relative"; validate_failures=1 ;;
    esac
  done
  echo
  if (( validate_failures != 0 )); then
    echo "Validation failed: one or more patches conflict."
    exit 1
  fi
  echo "Validation passed."
  exit 0
fi

echo "============================================================"
echo " AzerothCore core patch installer"
echo "============================================================"
echo

echo "Repository : $REPO"
echo "Patch dir  : $PATCH_DIR"
echo "Files      : ${#PATCH_FILES[@]}"
echo

apply_failures=0
for patch_file in "${PATCH_FILES[@]}"; do
  if ! apply_patch "$patch_file"; then
    apply_failures=1
    break
  fi
done

echo

if (( apply_failures != 0 )); then
  echo "Patch installation failed."
  exit 1
fi

echo "All core patches applied successfully."
