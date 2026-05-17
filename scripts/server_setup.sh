#!/bin/sh
# NHMT-EA Server Setup -- run ONCE on the Hetzner server
# Usage: sh server_setup.sh
set -e

SERVER_IP="178.105.16.51"
REPO="/opt/net-ea"
APP_USER="ymersha"

echo ""
echo "=================================================================="
echo "  NHMT-EA Server Setup -- Ubuntu 24.04"
echo "  Server: $SERVER_IP"
echo "=================================================================="
echo ""

echo "[1/7] Updating system packages..."
sudo apt-get update -q
sudo apt-get upgrade -y -q
sudo apt-get install -y -q git curl wget python3-pip ufw certbot python3-certbot-nginx

echo "[2/7] Installing Podman..."
sudo apt-get install -y -q podman
podman --version

echo "[3/7] Installing podman-compose..."
sudo pip3 install podman-compose --break-system-packages -q 2>/dev/null || \
  pip3 install podman-compose --break-system-packages -q
podman-compose --version 2>/dev/null || echo "  (podman-compose installed, restart shell)"

echo "[4/7] Installing Nginx..."
sudo apt-get install -y -q nginx
sudo systemctl enable nginx
sudo systemctl start  nginx
echo "  Nginx started"

echo "[5/7] Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw --force enable
sudo ufw status

echo "[6/7] Creating application directory..."
sudo mkdir -p "$REPO"
sudo chown "$APP_USER:$APP_USER" "$REPO"
echo "  App dir: $REPO"

echo "[7/7] Creating Podman data volume..."
podman volume create net-ea-data 2>/dev/null || true
echo "  Volume: net-ea-data ready"

echo ""
echo "=================================================================="
echo "  Server setup complete!"
echo ""
echo "  Next -- from your laptop:"
echo "  bash scripts/server_deploy.sh"
echo "=================================================================="
echo ""
