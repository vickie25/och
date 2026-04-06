#!/usr/bin/env bash
# Server-side Docker steps for recipe views (password via SSHPASS only).
set -euo pipefail

: "${SSHPASS:?Set SSHPASS for SSH (do not hardcode secrets)}"
SERVER="${DEPLOY_SSH_HOST:-administrator@69.30.235.220}"
PORT="${DEPLOY_SSH_PORT:-22}"

sshpass -e ssh -p "${PORT}" -o StrictHostKeyChecking=no "${SERVER}" << 'EOF'
echo "Stopping Django container..."
sudo docker stop ongozacyberhub_django

echo "Copying updated code..."
sudo docker cp ongozacyberhub_django:/app/recipes/views.py /tmp/recipes_views.py.backup 2>/dev/null || true

echo "Copy the updated recipes/views.py to the server, then:"
echo "  scp recipes/views.py ${SERVER}:/tmp/"
echo "Restarting Django container..."
sudo docker start ongozacyberhub_django

echo "Checking container status..."
sudo docker ps | grep django
EOF
