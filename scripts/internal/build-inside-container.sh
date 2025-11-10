#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
LANG_CODE=${BUILD_LANG:-zh}
TARGETS_RAW=${BUILD_TARGETS:-"html html-chunk epub pdf"}
SVN_BASE=${POSS_SVN_BASE:-https://svn.red-bean.com/repos/producingoss/trunk}
FOP_MEMORY=${FOP_OPTS:-"-Xms512m -Xmx1024m"}
CHUNK_DIR=${HTML_CHUNK_DIR_OVERRIDE:-html-chunk}

log() {
  printf '[build:%s] %s\n' "$LANG_CODE" "$*"
}

ensure_lang_exists() {
  if [ ! -d "${REPO_ROOT}/book/${LANG_CODE}" ]; then
    echo "Language directory book/${LANG_CODE} does not exist" >&2
    exit 1
  fi
}

ensure_tooling() {
  mkdir -p "${REPO_ROOT}/book"
  if [ ! -d "${REPO_ROOT}/book/tools" ]; then
    log "Fetching upstream tools/ from ${SVN_BASE}"
    svn export --quiet "${SVN_BASE}/tools" "${REPO_ROOT}/book/tools"
  fi
  if [ ! -f "${REPO_ROOT}/book/lang-makefile" ]; then
    log "Fetching lang-makefile"
    svn export --quiet "${SVN_BASE}/lang-makefile" "${REPO_ROOT}/book/lang-makefile"
  fi
  if [ ! -f "${REPO_ROOT}/book/styles.css" ]; then
    log "Fetching shared styles.css"
    svn export --quiet "${SVN_BASE}/styles.css" "${REPO_ROOT}/book/styles.css"
  fi
}

generate_book_xml() {
  local in="${REPO_ROOT}/book/${LANG_CODE}/book.xml.in"
  local out="${REPO_ROOT}/book/${LANG_CODE}/book.xml"
  if [ -f "$in" ]; then
    local git_ref="unknown"
    if git -C "$REPO_ROOT" rev-parse --short=12 HEAD >/dev/null 2>&1; then
      git_ref="$(git -C "$REPO_ROOT" rev-parse --short=12 HEAD)"
    fi
    local build_date
    build_date="$(date -u +'%d %b %Y')"
    local version_string="${git_ref} (${build_date})"
    log "Generating book.xml with version ${version_string}"
    sed "s|__SEE ../aggrevision SCRIPT__|${version_string}|g" "$in" > "$out"
  elif [ ! -f "$out" ]; then
    echo "Missing book.xml for ${LANG_CODE} (and no book.xml.in to derive from)." >&2
    exit 1
  fi
}

run_targets() {
  local targets=()
  # shellcheck disable=SC2086
  for target in ${TARGETS_RAW}; do
    targets+=("$target")
  done
  if [ ${#targets[@]} -eq 0 ]; then
    echo "No build targets requested" >&2
    exit 1
  fi

  export FOP_OPTS="$FOP_MEMORY"
  for target in "${targets[@]}"; do
    log "Running make target: ${target}"
    make -C "${REPO_ROOT}/book/${LANG_CODE}" \
         -f ../lang-makefile \
         HTML_CHUNK_DIR="$CHUNK_DIR" \
         "$target"
  done
}

summarize_outputs() {
  local lang_dir="${REPO_ROOT}/book/${LANG_CODE}"
  log "Generated files:"
  ls -1 "${lang_dir}"/producingoss* 2>/dev/null || true
  if [ -d "${lang_dir}/html-chunk" ]; then
    ls -1 "${lang_dir}/html-chunk" | head -n 5 >/tmp/html-chunk-list || true
    log "html-chunk sample files:"
    cat /tmp/html-chunk-list 2>/dev/null || true
  fi
}

ensure_lang_exists
ensure_tooling
generate_book_xml
run_targets
summarize_outputs
