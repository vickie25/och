#!/usr/bin/env bash
# Remote pull + quick_update over SSH using sshpass (password via env only — never commit secrets).
#
# Usage:
#   export SSHPASS='your-ssh-password'
#   export SSH_USER_HOST='administrator@69.30.235.220'   # optional
#   export SSH_PORT='22'                                  # optional
#   bash deploy/sshpass_remote_update.sh
#
# Requires: sshpass (brew install sshpass / apt install sshpass)

set -euo pipefail

if ! command -v sshpass &>/dev/null; then
  echo "❌ sshpass not found. Install it (e.g. brew install hudochenkov/sshpass/sshpass)."
  exit 1
fi

if [ -z "${SSHPASS:-}" ]; then
  echo "❌ Set SSHPASS in the environment (example: export SSHPASS='...'). Do not put passwords in this file."
  exit 1
fi

SERVER="${SSH_USER_HOST:-administrator@69.30.235.220}"
PORT="${SSH_PORT:-22}"

echo "=========================================="
echo "Remote update via sshpass → ${SERVER} (port ${PORT})"
echo "=========================================="

sshpass -e ssh -o StrictHostKeyChecking=no -p "${PORT}" "${SERVER}" bash -s <<'REMOTE'
set -euo pipefail
REPO="${REMOTE_REPO_DIR:-$HOME/ongozacyberhub}"
cd "$REPO" || { echo "❌ Directory not found: $REPO (set REMOTE_REPO_DIR on the server if different)"; exit 1; }

echo "🔄 git pull..."
git pull origin main || git pull origin master

if [ -f deploy/quick_update.sh ]; then
  chmod +x deploy/quick_update.sh 2>/dev/null || true
  bash deploy/quick_update.sh
else
  echo "❌ deploy/quick_update.sh missing"
  exit 1
fi

echo "✅ Remote update finished"
REMOTE

echo ""
echo "✅ Local sshpass_remote_update completed"
