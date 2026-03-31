#!/bin/bash

# Server update script for Ongoza CyberHub
# Run this script on the server (69.30.235.220)

echo "Starting server update..."

# Navigate to project directory
cd /root/och

# Stop running containers
echo "Stopping Docker containers..."
docker-compose down

# Pull latest changes from GitHub
echo "Pulling latest changes from GitHub..."
git pull origin main

# Rebuild and start containers with latest code
echo "Rebuilding and starting containers..."
docker-compose up --build -d

# Wait for services to be healthy
echo "Waiting for services to start..."
sleep 30

# Check container status
echo "Checking container status..."
docker-compose ps

# Show logs for any issues
echo "Showing recent logs..."
docker-compose logs --tail=50

echo "Server update complete!"
echo "Frontend: http://69.30.235.220"
echo "Backend API: http://69.30.235.220/api"
