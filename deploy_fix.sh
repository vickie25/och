#!/bin/bash

echo "Deploying recipe permission fix to server..."

# Copy the fixed file to server
scp /Users/airm1/Projects/och/backend/django_app/recipes/views.py administrator@69.30.235.220:/tmp/views.py_fixed

# Deploy to Docker container
sshpass -p 'Ongoza@#1' ssh administrator@69.30.235.220 << 'EOF'
echo "Copying fixed file to Django container..."
sudo docker cp /tmp/views.py_fixed ongozacyberhub_django:/app/recipes/views.py

echo "Restarting Django container to apply changes..."
sudo docker restart ongozacyberhub_django

echo "Waiting for container to be healthy..."
sleep 10

echo "Checking container status..."
sudo docker ps | grep django

echo "Checking Django logs..."
sudo docker logs ongozacyberhub_django --tail 10
EOF

echo "Deployment complete!"
echo "Test the recipe generation in admin panel."
