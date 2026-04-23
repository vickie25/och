#!/usr/bin/env bash
# Free disk without deleting named images you still use. Safe to run periodically on the VPS.
# Review `docker system df` before/after.

set -euo pipefail

echo "=== Before ==="
docker system df 2>/dev/null || true

echo "=== Prune dangling images (untagged layers) ==="
docker image prune -f

echo "=== Prune build cache older than 14 days (BuildKit) ==="
if docker buildx version >/dev/null 2>&1; then
  docker builder prune -f --filter "until=336h" 2>/dev/null || docker builder prune -f
else
  docker builder prune -f 2>/dev/null || true
fi

echo "=== After ==="
docker system df 2>/dev/null || true
