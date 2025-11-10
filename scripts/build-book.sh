#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/build-book.sh [LANG ...]

Build the Producing OSS book for each language directory using a Dockerized toolchain.
If no LANG is supplied, "zh" is assumed.

Environment variables:
  BUILD_TARGETS        Make targets to run (default: "html html-chunk epub pdf")
  POSS_BUILDER_IMAGE   Docker image tag to use/build (default: producingoss-builder:latest)
  POSS_DOCKERFILE      Path to the Dockerfile (default: docker/builder.Dockerfile)
  POSS_SVN_BASE        Override upstream SVN base URL.
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to run this script." >&2
  exit 1
fi

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
LANGS=("$@")
if [ ${#LANGS[@]} -eq 0 ]; then
  LANGS=(zh)
fi

IMAGE_TAG=${POSS_BUILDER_IMAGE:-producingoss-builder:latest}
DOCKERFILE=${POSS_DOCKERFILE:-docker/builder.Dockerfile}
TARGETS=${BUILD_TARGETS:-"html html-chunk epub pdf"}

# Build (or update) the container image.
DOCKER_BUILD_ARGS=(build "-t" "$IMAGE_TAG" "-f" "$DOCKERFILE" "$REPO_ROOT")
echo "[docker] ${DOCKER_BUILD_ARGS[*]}"
docker "${DOCKER_BUILD_ARGS[@]}"

for lang in "${LANGS[@]}"; do
  echo "[docker-run] Building language '${lang}' with targets: ${TARGETS}"
  docker run --rm \
    -v "$REPO_ROOT":/workspace \
    -w /workspace \
    -e BUILD_LANG="$lang" \
    -e BUILD_TARGETS="$TARGETS" \
    -e POSS_SVN_BASE="${POSS_SVN_BASE:-}" \
    -e FOP_OPTS="${FOP_OPTS:-}" \
    "$IMAGE_TAG" \
    bash -lc "./scripts/internal/build-inside-container.sh"
done
