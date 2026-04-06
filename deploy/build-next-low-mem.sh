#!/usr/bin/env bash
# Build Next.js image on a small VPS: limit BuildKit parallelism so deps/builder/runner
# steps do not spike RAM/CPU at the same time. Run from repo root (e.g. /var/www/och).
#
# Usage: bash deploy/build-next-low-mem.sh
# Optional: SWAP_PATH / SIZE_MB — see deploy/ensure-swap-2g.sh

set -euo pipefail
cd "$(dirname "$0")/.."

if docker compose version >/dev/null 2>&1; then
  DC=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  DC=(docker-compose)
else
  echo "docker compose not found" >&2
  exit 1
fi

# One BuildKit vertex at a time — avoids deps + other stages fighting for RAM
P="${BUILDKIT_MAX_PARALLELISM:-1}"
export BUILDKIT_MAX_PARALLELISM="$P"
export DOCKER_BUILDKIT_MAX_PARALLELISM="${DOCKER_BUILDKIT_MAX_PARALLELISM:-$P}"

echo "BUILDKIT_MAX_PARALLELISM=$BUILDKIT_MAX_PARALLELISM DOCKER_BUILDKIT_MAX_PARALLELISM=$DOCKER_BUILDKIT_MAX_PARALLELISM"
if [ "${PRUNE_BUILDER:-}" = "1" ]; then
  echo "PRUNE_BUILDER=1: docker builder prune -f"
  docker builder prune -f 2>/dev/null || true
fi
BUILD_ARGS=()
if [ "${NO_CACHE:-}" = "1" ]; then
  BUILD_ARGS+=(--no-cache)
  echo "NO_CACHE=1: full rebuild (use once after a failed/corrupt deps layer)"
fi
echo "Running: ${DC[*]} build ${BUILD_ARGS[*]} nextjs"
"${DC[@]}" build "${BUILD_ARGS[@]}" nextjs

echo "Running: ${DC[*]} up -d nextjs"
"${DC[@]}" up -d nextjs

docker ps --filter name=ongozacyberhub_nextjs --format '{{.Names}} {{.Status}}'
