#!/bin/sh
# NHMT-EA Server Deploy -- run from your LAPTOP
# Builds images, transfers to server, starts containers
# Usage: sh scripts/server_deploy.sh
set -e

SERVER="ymersha@178.105.16.51"
REPO="/opt/net-ea"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "=================================================================="
echo "  NHMT-EA Deploy to Hetzner"
echo "  Server: 178.105.16.51"
echo "=================================================================="
echo ""

echo "[1/5] Building images locally..."
podman build -f "$ROOT/podman/Containerfile.backend"  \
  -t localhost/nhmt-ea-backend:latest  "$ROOT"
podman build -f "$ROOT/podman/Containerfile.frontend" \
  -t localhost/nhmt-ea-frontend:latest "$ROOT"
echo "  Images built"

echo "[2/5] Exporting images..."
podman save localhost/nhmt-ea-backend:latest  | gzip > /tmp/nhmt-ea-backend.tar.gz
podman save localhost/nhmt-ea-frontend:latest | gzip > /tmp/nhmt-ea-frontend.tar.gz
echo "  Backend:  $(du -sh /tmp/nhmt-ea-backend.tar.gz  | cut -f1)"
echo "  Frontend: $(du -sh /tmp/nhmt-ea-frontend.tar.gz | cut -f1)"

echo "[3/5] Transferring to server..."
scp /tmp/nhmt-ea-backend.tar.gz  "$SERVER:/tmp/"
scp /tmp/nhmt-ea-frontend.tar.gz "$SERVER:/tmp/"
scp "$ROOT/.env"                  "$SERVER:$REPO/.env"
ssh "$SERVER" "mkdir -p $REPO/scripts $REPO/podman"
scp -r "$ROOT/podman/"            "$SERVER:$REPO/"
scp -r "$ROOT/scripts/"           "$SERVER:$REPO/"
echo "  Files transferred"

echo "[4/5] Loading images on server..."
ssh "$SERVER" "podman load < /tmp/nhmt-ea-backend.tar.gz  && \
               podman load < /tmp/nhmt-ea-frontend.tar.gz && \
               rm -f /tmp/nhmt-ea-backend.tar.gz /tmp/nhmt-ea-frontend.tar.gz"
echo "  Images loaded"

echo "[5/5] Starting containers on server..."
ssh "$SERVER" "sh $REPO/scripts/podman_run.sh"

echo "  Setting up Nginx proxy..."
ssh "$SERVER" "sudo cp $REPO/podman/nginx-proxy.conf /etc/nginx/sites-available/nhmt-ea && \
               sudo ln -sf /etc/nginx/sites-available/nhmt-ea \
                           /etc/nginx/sites-enabled/nhmt-ea && \
               sudo rm -f /etc/nginx/sites-enabled/default && \
               sudo nginx -t && sudo systemctl reload nginx"

rm -f /tmp/nhmt-ea-backend.tar.gz /tmp/nhmt-ea-frontend.tar.gz

echo ""
echo "=================================================================="
echo "  Deployment complete!"
echo ""
echo "  Frontend : http://178.105.16.51"
echo "  Backend  : http://178.105.16.51/api"
echo "  API docs : http://178.105.16.51/api/docs"
echo ""
echo "  Monitor:"
echo "  ssh $SERVER 'sh $REPO/scripts/podman_status.sh'"
echo "=================================================================="
echo ""
