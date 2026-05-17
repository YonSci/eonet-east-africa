#!/bin/sh
# NHMT-EA Server Update -- run ON THE SERVER
# Usage: sh /opt/net-ea/scripts/server_update.sh
set -e

REPO="/opt/net-ea"
echo ""
echo "=== NHMT-EA Update ==="
echo ""
cd "$REPO"

if [ -d ".git" ]; then
  echo "[1/3] Pulling latest code..."
  git pull origin main
fi

echo "[2/3] Rebuilding images..."
podman build -f podman/Containerfile.backend  -t localhost/nhmt-ea-backend:latest  .
podman build -f podman/Containerfile.frontend -t localhost/nhmt-ea-frontend:latest .

echo "[3/3] Restarting containers..."
sh scripts/podman_stop.sh
sh scripts/podman_run.sh

echo "=== Update complete -- http://178.105.16.51 ==="
echo ""
