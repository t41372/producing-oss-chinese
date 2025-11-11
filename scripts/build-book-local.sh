#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/build-book-local.sh [LANG ...]

Build the Producing OSS book for each language directory using the toolchain
installed directly on the host machine (no Docker).
If no LANG is supplied, "zh" is assumed.

Environment variables:
  BUILD_TARGETS              Make targets to run (default: "html html-chunk epub pdf")
  POSS_SVN_BASE              Override upstream SVN base URL.
  FOP_OPTS                   JVM options for Apache FOP (default handled by build script)
  HTML_CHUNK_DIR_OVERRIDE    Override the html-chunk output directory name.
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
INTERNAL_SCRIPT="${REPO_ROOT}/scripts/internal/build-inside-container.sh"

if [[ ! -x "$INTERNAL_SCRIPT" ]]; then
  echo "Internal build script not found or not executable: $INTERNAL_SCRIPT" >&2
  exit 1
fi

LANGS=("$@")
if [ ${#LANGS[@]} -eq 0 ]; then
  LANGS=(zh)
fi

TARGETS=${BUILD_TARGETS:-"html html-chunk epub pdf"}

ensure_command() {
  local cmd=$1
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Required command '$cmd' not found in PATH" >&2
    exit 1
  fi
}

# Basic tooling needed outside the container. DocBook/FOP binaries are invoked via make.
ensure_command svn
ensure_command make

for lang in "${LANGS[@]}"; do
  echo "[local] Building language '${lang}' with targets: ${TARGETS}"
  BUILD_LANG="$lang" \
  BUILD_TARGETS="$TARGETS" \
  POSS_SVN_BASE="${POSS_SVN_BASE:-}" \
  FOP_OPTS="${FOP_OPTS:-}" \
  HTML_CHUNK_DIR_OVERRIDE="${HTML_CHUNK_DIR_OVERRIDE:-}" \
    bash "$INTERNAL_SCRIPT"
done
