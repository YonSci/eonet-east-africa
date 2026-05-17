#!/bin/sh
# NHMT-EA Podman run script
# Usage: sh scripts/podman_run.sh
set -e

if ! command -v podman >/dev/null 2>&1; then
  echo "Error: podman command not found."
  echo "Install Podman in this shell/WSL environment, then retry."
  exit 127
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "=== NHMT-EA Podman Start ==="
echo ""

# Create data volume if needed
podman volume create net-ea-data 2>/dev/null || true
echo "  Volume: net-ea-data ready"

# Stop and remove existing containers (current + legacy names)
podman stop  nhmt-ea-backend  2>/dev/null || true
podman stop  nhmt-ea-frontend 2>/dev/null || true
podman rm    nhmt-ea-backend  2>/dev/null || true
podman rm    nhmt-ea-frontend 2>/dev/null || true
podman stop  net-ea-backend   2>/dev/null || true
podman stop  net-ea-frontend  2>/dev/null || true
podman rm    net-ea-backend   2>/dev/null || true
podman rm    net-ea-frontend  2>/dev/null || true

# Remove old pod if exists, recreate (current + legacy names)
podman pod rm nhmt-ea 2>/dev/null || true
podman pod stop net-ea 2>/dev/null || true
podman pod rm   net-ea 2>/dev/null || true
podman pod create \
  --name nhmt-ea \
  --publish 8000:8000 \
  --publish 3000:80

echo "[1/2] Starting backend..."
podman run -d \
  --name nhmt-ea-backend \
  --pod nhmt-ea \
  --env-file "$ROOT/.env" \
  --volume net-ea-data:/app/data:Z \
  --restart unless-stopped \
  localhost/nhmt-ea-backend:latest
echo "  Backend started"

echo "  Waiting for backend to be healthy..."
i=0
while [ $i -lt 20 ]; do
  if podman healthcheck run nhmt-ea-backend 2>/dev/null | grep -q "healthy" 2>/dev/null; then
    echo "  Backend healthy"
    break
  fi
  i=$((i + 1))
  printf "."
  sleep 2
done
echo ""

echo "[2/2] Starting frontend..."
podman run -d \
  --name nhmt-ea-frontend \
  --pod nhmt-ea \
  --restart unless-stopped \
  localhost/nhmt-ea-frontend:latest
echo "  Frontend started"

echo ""
echo "=== NHMT-EA is running ==="
echo ""
echo "  Frontend : http://localhost:3000"
echo "  Backend  : http://localhost:8000"
echo "  API docs : http://localhost:8000/docs"
echo ""
echo "  Logs   : sh scripts/podman_logs.sh"
echo "  Status : sh scripts/podman_status.sh"
echo "  Stop   : sh scripts/podman_stop.sh"
echo ""
