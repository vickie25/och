#!/usr/bin/env bash
# Run ON THE SERVER from repo root (e.g. /var/www/och). Makes working tree match origin/main, then refreshes containers.
# Intentionally destructive of local edits on the server — use when prod must match GitHub main.
set -euo pipefail
cd /var/www/och
git fetch origin
git reset --hard origin/main
docker compose pull nextjs django fastapi || true
docker compose up -d
docker compose ps
echo "HEAD: $(git log -1 --oneline)"
