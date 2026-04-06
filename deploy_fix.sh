#!/usr/bin/env bash
# One-off: copy recipes/views.py into Django container on the server.
# Requires: sshpass, SSHPASS in environment (never commit passwords).
set -euo pipefail

: "${SSHPASS:?Set SSHPASS for SSH (do not hardcode secrets)}"
SERVER="${DEPLOY_SSH_HOST:-administrator@69.30.235.220}"
PORT="${DEPLOY_SSH_PORT:-22}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Deploying recipe permission fix to server..."

sshpass -e scp -P "${PORT}" -o StrictHostKeyChecking=no \
  "${ROOT}/backend/django_app/recipes/views.py" \
  "${SERVER}:/tmp/views.py_fixed"

sshpass -e ssh -p "${PORT}" -o StrictHostKeyChecking=no "${SERVER}" << 'EOF'
echo "Copying fixed file to Django container..."
sudo docker cp /tmp/views.py_fixed ongozacyberhub_django:/app/recipes/views.py

echo "Restarting Django container to apply changes..."
sudo docker restart ongozacyberhub_django

echo "Waiting for the container to be healthy..."
sleep 10

echo "Checking container status..."
sudo docker ps | grep django

echo "Checking Django logs..."
sudo docker logs ongozacyberhub_django --tail 10
EOF

echo "Deployment complete!"
echo "Test the recipe generation in admin panel."
