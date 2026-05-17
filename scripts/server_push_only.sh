#!/bin/sh
# NHMT-EA lightweight push -- transfer pre-built images to server
# Usage: sh scripts/server_push_only.sh
set -e

SERVER="ymersha@178.105.16.51"
REPO="/opt/net-ea"

echo ""
echo "=== Pushing NHMT-EA images to server ==="
echo ""

echo "Exporting backend..."
podman save localhost/nhmt-ea-backend:latest | gzip > /tmp/nhmt-ea-backend.tar.gz
echo "  Size: $(du -sh /tmp/nhmt-ea-backend.tar.gz | cut -f1)"
scp /tmp/nhmt-ea-backend.tar.gz "$SERVER:/tmp/"

echo "Exporting frontend..."
podman save localhost/nhmt-ea-frontend:latest | gzip > /tmp/nhmt-ea-frontend.tar.gz
echo "  Size: $(du -sh /tmp/nhmt-ea-frontend.tar.gz | cut -f1)"
scp /tmp/nhmt-ea-frontend.tar.gz "$SERVER:/tmp/"

echo "Loading and restarting on server..."
ssh "$SERVER" "podman load < /tmp/nhmt-ea-backend.tar.gz  && \
               podman load < /tmp/nhmt-ea-frontend.tar.gz && \
               rm -f /tmp/nhmt-ea-*.tar.gz && \
               sh $REPO/scripts/podman_run.sh"

rm -f /tmp/nhmt-ea-backend.tar.gz /tmp/nhmt-ea-frontend.tar.gz
echo ""
echo "Done -- http://178.105.16.51"
echo ""
