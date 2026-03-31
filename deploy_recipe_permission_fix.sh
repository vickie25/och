#!/bin/bash

# Deploy recipe permission fix to server
sshpass -p 'Ongoza@#1' ssh administrator@69.30.235.220 << 'EOF'
echo "Stopping Django container..."
sudo docker stop ongozacyberhub_django

echo "Copying updated code..."
# Create a backup of the current file
sudo docker cp ongozacyberhub_django:/app/recipes/views.py /tmp/recipes_views.py.backup

# Copy the updated file (you'll need to manually copy this from local)
echo "Please copy the updated recipes/views.py file to the server"
echo "Run: scp recipes/views.py administrator@69.30.235.220:/tmp/"

echo "Restarting Django container..."
sudo docker start ongozacyberhub_django

echo "Checking container status..."
sudo docker ps | grep django

echo "Deployment complete!"
EOF
