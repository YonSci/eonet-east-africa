"""
setup_hetzner_deploy.py
-----------------------
Generates everything needed to deploy NET-EA on the Hetzner Ubuntu 24.04 server.

Creates:
  scripts/server_setup.sh      -- run ONCE on the server (installs Podman, Nginx, SSL)
  scripts/server_deploy.sh     -- run to deploy / redeploy from your laptop
  scripts/server_update.sh     -- run on server to pull latest code and rebuild
  podman/nginx-proxy.conf      -- Nginx reverse proxy config (port 80/443)
  podman/Caddyfile             -- alternative: Caddy auto-SSL (simpler than Nginx)
  HETZNER_DEPLOY.md            -- full step-by-step guide

Usage after running this script:
  1. python setup_hetzner_deploy.py
  2. scp scripts/server_setup.sh ymersha@178.105.16.51:~/
  3. ssh ymersha@178.105.16.51 "bash ~/server_setup.sh"
  4. bash scripts/server_deploy.sh
"""

import argparse
from pathlib import Path

try:
    from colorama import Fore, Style, init as _ci
    _ci(autoreset=True)
    def ok(m):  print(f"{Fore.GREEN}  [+]{Style.RESET_ALL} {m}")
    def ow(m):  print(f"{Fore.YELLOW}  [~]{Style.RESET_ALL} {m}")
    def hdr(m): print(f"\n{Fore.CYAN}{Style.BRIGHT}{m}{Style.RESET_ALL}")
except ImportError:
    def ok(m):  print(f"  [+] {m}")
    def ow(m):  print(f"  [~] {m}")
    def hdr(m): print(f"\n{m}")

SERVER_IP   = "178.105.16.51"
SERVER_USER = "ymersha"
SERVER_SSH  = f"{SERVER_USER}@{SERVER_IP}"
REPO_DIR    = "/opt/net-ea"

FILES = {}

# =============================================================================
# scripts/server_setup.sh
# Run ONCE on the server after first SSH login
# =============================================================================
FILES["scripts/server_setup.sh"] = f"""#!/bin/bash
# NET-EA Server Setup -- run ONCE on {SERVER_IP}
# Usage: bash server_setup.sh
set -e

echo ""
echo "==================================================================="
echo "  NET-EA Server Setup -- Ubuntu 24.04"
echo "  Server: {SERVER_IP}"
echo "==================================================================="
echo ""

# -- System update --
echo "[1/7] Updating system packages..."
sudo apt update -q && sudo apt upgrade -y -q
sudo apt install -y -q git curl wget python3-pip ufw certbot python3-certbot-nginx

# -- Podman --
echo "[2/7] Installing Podman..."
sudo apt install -y -q podman
podman --version

# -- podman-compose --
echo "[3/7] Installing podman-compose..."
sudo pip3 install podman-compose --break-system-packages -q
podman-compose --version

# -- Nginx (reverse proxy for SSL) --
echo "[4/7] Installing Nginx..."
sudo apt install -y -q nginx
sudo systemctl enable nginx
sudo systemctl start nginx
echo "  Nginx installed and started"

# -- Firewall --
echo "[5/7] Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'   # ports 80 and 443
sudo ufw allow 8000/tcp       # backend API (optional -- remove in production)
sudo ufw allow 3000/tcp       # frontend direct (optional -- remove in production)
sudo ufw --force enable
sudo ufw status
echo "  Firewall configured"

# -- Application directory --
echo "[6/7] Creating application directory..."
sudo mkdir -p {REPO_DIR}
sudo chown {SERVER_USER}:{SERVER_USER} {REPO_DIR}
echo "  App dir: {REPO_DIR}"

# -- Podman data volume --
echo "[7/7] Creating Podman volume..."
podman volume create net-ea-data 2>/dev/null || true
echo "  Volume: net-ea-data ready"

echo ""
echo "==================================================================="
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. On your LAPTOP: bash scripts/server_deploy.sh"
echo "  2. Configure DNS: point your domain A record to {SERVER_IP}"
echo "  3. Get SSL cert: sudo certbot --nginx -d yourdomain.com"
echo "==================================================================="
echo ""
"""

# =============================================================================
# scripts/server_deploy.sh
# Run from your LAPTOP to build images, push to server, and start containers
# =============================================================================
FILES["scripts/server_deploy.sh"] = f"""#!/bin/bash
# NET-EA Server Deploy -- run from your LAPTOP
# Builds images locally, transfers to server, starts containers
# Usage: bash scripts/server_deploy.sh
set -e

SERVER="{SERVER_SSH}"
REPO="{REPO_DIR}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "==================================================================="
echo "  NET-EA Deploy to Hetzner Server"
echo "  Server: {SERVER_IP}"
echo "==================================================================="
echo ""

# Step 1: Build images locally
echo "[1/5] Building Podman images locally..."
podman build -f "$ROOT/podman/Containerfile.backend"  \\
  -t localhost/net-ea-backend:latest  "$ROOT"
podman build -f "$ROOT/podman/Containerfile.frontend" \\
  -t localhost/net-ea-frontend:latest "$ROOT"
echo "  Images built"

# Step 2: Export images to compressed archives
echo "[2/5] Exporting images (this may take a minute)..."
podman save localhost/net-ea-backend:latest  | gzip > /tmp/net-ea-backend.tar.gz
podman save localhost/net-ea-frontend:latest | gzip > /tmp/net-ea-frontend.tar.gz
echo "  Backend:  $(du -sh /tmp/net-ea-backend.tar.gz  | cut -f1)"
echo "  Frontend: $(du -sh /tmp/net-ea-frontend.tar.gz | cut -f1)"

# Step 3: Transfer images + config files to server
echo "[3/5] Transferring to server..."
scp /tmp/net-ea-backend.tar.gz  "$SERVER:/tmp/"
scp /tmp/net-ea-frontend.tar.gz "$SERVER:/tmp/"
scp "$ROOT/.env"                 "$SERVER:$REPO/.env"
scp -r "$ROOT/podman"            "$SERVER:$REPO/"
scp -r "$ROOT/scripts"           "$SERVER:$REPO/"
scp -r "$ROOT/backend"           "$SERVER:$REPO/"
scp "$ROOT/requirements.txt"     "$SERVER:$REPO/"
echo "  Files transferred"

# Step 4: Load images on server
echo "[4/5] Loading images on server..."
ssh "$SERVER" "podman load < /tmp/net-ea-backend.tar.gz && \\
               podman load < /tmp/net-ea-frontend.tar.gz && \\
               rm -f /tmp/net-ea-backend.tar.gz /tmp/net-ea-frontend.tar.gz"
echo "  Images loaded"

# Step 5: Start containers on server
echo "[5/5] Starting containers on server..."
ssh "$SERVER" "cd $REPO && bash scripts/podman_run.sh"

# Setup Nginx proxy
echo ""
echo "  Installing Nginx proxy config..."
ssh "$SERVER" "sudo cp $REPO/podman/nginx-proxy.conf /etc/nginx/sites-available/net-ea && \\
               sudo ln -sf /etc/nginx/sites-available/net-ea /etc/nginx/sites-enabled/net-ea && \\
               sudo rm -f /etc/nginx/sites-enabled/default && \\
               sudo nginx -t && sudo systemctl reload nginx"

echo ""
echo "==================================================================="
echo "  Deployment complete!"
echo ""
echo "  Frontend : http://{SERVER_IP}"
echo "  Backend  : http://{SERVER_IP}/api"
echo "  API docs : http://{SERVER_IP}/api/docs"
echo ""
echo "  For HTTPS (run on server after pointing domain):"
echo "    sudo certbot --nginx -d yourdomain.com"
echo ""
echo "  Server management:"
echo "    ssh {SERVER_SSH} 'cd {REPO_DIR} && bash scripts/podman_status.sh'"
echo "    ssh {SERVER_SSH} 'cd {REPO_DIR} && bash scripts/podman_logs.sh'"
echo "==================================================================="
echo ""

# Cleanup local tmp files
rm -f /tmp/net-ea-backend.tar.gz /tmp/net-ea-frontend.tar.gz
"""

# =============================================================================
# scripts/server_update.sh
# Run on the server to pull latest code and rebuild without transferring images
# =============================================================================
FILES["scripts/server_update.sh"] = f"""#!/bin/bash
# NET-EA Server Update -- run ON THE SERVER
# Pulls latest code from GitHub and rebuilds containers
# Usage: ssh {SERVER_SSH} "bash {REPO_DIR}/scripts/server_update.sh"
set -e

REPO="{REPO_DIR}"

echo ""
echo "=== NET-EA Update ==="
echo ""

cd "$REPO"

# Pull latest from GitHub (if using git)
if [ -d ".git" ]; then
  echo "[1/3] Pulling latest code..."
  git pull origin main
fi

# Rebuild images
echo "[2/3] Rebuilding images..."
podman build -f podman/Containerfile.backend  -t localhost/net-ea-backend:latest  .
podman build -f podman/Containerfile.frontend -t localhost/net-ea-frontend:latest .

# Restart containers
echo "[3/3] Restarting containers..."
podman stop  net-ea-frontend net-ea-backend  2>/dev/null || true
podman rm    net-ea-frontend net-ea-backend  2>/dev/null || true
bash scripts/podman_run.sh

echo ""
echo "=== Update complete ==="
echo "  Frontend : http://{SERVER_IP}"
echo "  Backend  : http://{SERVER_IP}/api"
echo ""
"""

# =============================================================================
# scripts/server_push_only.sh
# Lightweight push -- no rebuild, just transfer already-built images
# =============================================================================
FILES["scripts/server_push_only.sh"] = f"""#!/bin/bash
# Lightweight server push -- transfers pre-built images to server
# Faster than server_deploy.sh -- use after server_deploy.sh has run once
# Usage: bash scripts/server_push_only.sh
set -e

SERVER="{SERVER_SSH}"
REPO="{REPO_DIR}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "=== Pushing images to {SERVER_IP} ==="
echo ""

# Export and transfer backend
echo "Exporting backend..."
podman save localhost/net-ea-backend:latest | gzip > /tmp/net-ea-backend.tar.gz
echo "  Size: $(du -sh /tmp/net-ea-backend.tar.gz | cut -f1)"
scp /tmp/net-ea-backend.tar.gz "$SERVER:/tmp/"

# Export and transfer frontend
echo "Exporting frontend..."
podman save localhost/net-ea-frontend:latest | gzip > /tmp/net-ea-frontend.tar.gz
echo "  Size: $(du -sh /tmp/net-ea-frontend.tar.gz | cut -f1)"
scp /tmp/net-ea-frontend.tar.gz "$SERVER:/tmp/"

# Load and restart on server
echo "Loading and restarting on server..."
ssh "$SERVER" "
  podman load < /tmp/net-ea-backend.tar.gz
  podman load < /tmp/net-ea-frontend.tar.gz
  rm -f /tmp/net-ea-*.tar.gz
  cd $REPO && bash scripts/podman_run.sh
"

rm -f /tmp/net-ea-*.tar.gz
echo ""
echo "Done -- http://{SERVER_IP}"
echo ""
"""

# =============================================================================
# podman/nginx-proxy.conf -- Nginx reverse proxy (HTTP, no SSL yet)
# =============================================================================
FILES["podman/nginx-proxy.conf"] = f"""# NET-EA Nginx Reverse Proxy
# Serves on port 80, proxies to Podman containers
# After certbot: SSL cert is auto-inserted between the two server blocks

server {{
    listen 80;
    server_name {SERVER_IP} _;     # replace with your domain after DNS setup

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Frontend -- served by Nginx in the net-ea-frontend container
    location / {{
        proxy_pass         http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }}

    # Backend API -- proxied under /api path
    location /api/ {{
        rewrite            ^/api/(.*)$ /$1 break;
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }}

    # Direct backend endpoints (EONET data)
    location ~ ^/(events|summary|status|alerts) {{
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_read_timeout 60s;
    }}

    # Logs
    access_log /var/log/nginx/net-ea-access.log;
    error_log  /var/log/nginx/net-ea-error.log;
}}
"""

# =============================================================================
# podman/Caddyfile -- simpler alternative to Nginx (auto-SSL, no certbot needed)
# =============================================================================
FILES["podman/Caddyfile"] = f"""# NET-EA Caddy config -- auto-SSL alternative to Nginx
# Install: sudo apt install -y caddy
# Config:  sudo cp podman/Caddyfile /etc/caddy/Caddyfile
# Reload:  sudo systemctl reload caddy
#
# Caddy automatically fetches and renews SSL certs from Let's Encrypt.
# Just replace the IP below with your domain name.

{SERVER_IP} {{
    # Or use your domain: yourdomain.com {{

    # Frontend
    reverse_proxy /* 127.0.0.1:3000

    # Backend API
    reverse_proxy /events/*  127.0.0.1:8000
    reverse_proxy /summary   127.0.0.1:8000
    reverse_proxy /status    127.0.0.1:8000
    reverse_proxy /alerts/*  127.0.0.1:8000

    # Logging
    log {{
        output file /var/log/caddy/net-ea.log
    }}
}}
"""

# =============================================================================
# HETZNER_DEPLOY.md
# =============================================================================
FILES["HETZNER_DEPLOY.md"] = f"""# NET-EA Hetzner Server Deployment Guide

**Server:** {SERVER_IP} (Ubuntu 24.04.4 LTS)
**User:** {SERVER_USER}

---

## Step 1 -- Server setup (run ONCE)

Copy and run the setup script on the server:

```bash
# From your laptop:
scp scripts/server_setup.sh {SERVER_SSH}:~/
ssh {SERVER_SSH} "bash ~/server_setup.sh"
```

This installs: Podman, podman-compose, Nginx, UFW firewall, certbot (SSL).

---

## Step 2 -- Deploy from your laptop

```bash
# Builds images, transfers to server, starts containers, configures Nginx
bash scripts/server_deploy.sh
```

Your app will be live at:

| Service  | URL |
|---|---|
| Frontend | http://{SERVER_IP} |
| Backend  | http://{SERVER_IP}/api |
| API docs | http://{SERVER_IP}/api/docs |

---

## Step 3 -- Add a domain + HTTPS (recommended)

1. Point your domain A record to `{SERVER_IP}` in your DNS provider
2. Wait 5-60 minutes for DNS propagation
3. On the server, get a free SSL certificate:

```bash
ssh {SERVER_SSH}
sudo nano /etc/nginx/sites-available/net-ea
# Change: server_name {SERVER_IP} _;
# To:     server_name yourdomain.com www.yourdomain.com;
sudo nginx -t && sudo systemctl reload nginx

sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
# Follow prompts -- certbot auto-renews every 90 days
```

Your app is now at `https://yourdomain.com` with auto-renewing SSL.

---

## Redeploying after code changes

**Option A -- From your laptop (full rebuild):**
```bash
# Edit code locally, then:
bash scripts/server_deploy.sh
```

**Option B -- Push images only (faster, no rebuild from scratch):**
```bash
podman build -f podman/Containerfile.backend  -t net-ea-backend:latest .
podman build -f podman/Containerfile.frontend -t net-ea-frontend:latest .
bash scripts/server_push_only.sh
```

**Option C -- From GitHub (if repo is on GitHub):**
```bash
# Push to GitHub from laptop:
git push origin main

# On server:
ssh {SERVER_SSH} "bash {REPO_DIR}/scripts/server_update.sh"
```

---

## Server management commands

All run from your laptop:

```bash
# Check status
ssh {SERVER_SSH} "cd {REPO_DIR} && bash scripts/podman_status.sh"

# Follow backend logs
ssh {SERVER_SSH} "cd {REPO_DIR} && bash scripts/podman_logs.sh backend"

# Follow frontend logs
ssh {SERVER_SSH} "cd {REPO_DIR} && bash scripts/podman_logs.sh frontend"

# Restart containers
ssh {SERVER_SSH} "cd {REPO_DIR} && bash scripts/podman_stop.sh && bash scripts/podman_run.sh"

# SSH into backend container (debugging)
ssh {SERVER_SSH} "podman exec -it net-ea-backend bash"

# View subscription data (stored in volume)
ssh {SERVER_SSH} "podman exec net-ea-backend cat /app/data/subscriptions.json"

# Copy subscription data to laptop
ssh {SERVER_SSH} "podman exec net-ea-backend cat /app/data/subscriptions.json" > subscriptions.json
```

---

## Auto-start on server reboot (Quadlet / systemd)

```bash
ssh {SERVER_SSH}
mkdir -p ~/.config/containers/systemd
cp {REPO_DIR}/podman/quadlet/* ~/.config/containers/systemd/

# Create env file for backend
mkdir -p ~/.config/net-ea
cp {REPO_DIR}/.env ~/.config/net-ea/backend.env

systemctl --user daemon-reload
systemctl --user enable --now net-ea.service

# Verify it started
systemctl --user status net-ea.service

# Enable lingering so service runs even when you're not logged in
loginctl enable-linger {SERVER_USER}
```

Now NET-EA restarts automatically on server reboot.

---

## Firewall reference

```bash
sudo ufw status        # show current rules
sudo ufw allow 443/tcp # HTTPS (if not using 'Nginx Full')
sudo ufw deny 3000/tcp # close direct container port in production
sudo ufw deny 8000/tcp # close direct backend port in production (use Nginx proxy instead)
```

---

## Troubleshooting

**Containers not starting:**
```bash
ssh {SERVER_SSH} "podman ps -a"
ssh {SERVER_SSH} "podman logs net-ea-backend"
```

**Nginx not proxying correctly:**
```bash
ssh {SERVER_SSH} "sudo nginx -t"
ssh {SERVER_SSH} "sudo cat /var/log/nginx/net-ea-error.log"
```

**Port 3000/8000 not accessible:**
```bash
ssh {SERVER_SSH} "sudo ufw status"
ssh {SERVER_SSH} "podman ps"  # verify containers running
```

**Images not loading on server:**
```bash
ssh {SERVER_SSH} "podman images"  # check images are present
```

---

*NET-EA v3.0 -- Yonas Mersha -- Y.Mersha@cgiar.org -- ILRI*
"""

# =============================================================================
# Builder
# =============================================================================
def build(root: Path):
    hdr(f"Generating Hetzner deployment files in: {root}")
    created = updated = 0

    for rel, content in FILES.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        (ow if existed else ok)(("update  " if existed else "create  ") + rel)
        if existed: updated += 1
        else: created += 1

    # Make scripts executable
    for script in (root / "scripts").glob("server_*.sh"):
        script.chmod(script.stat().st_mode | 0o755)
        ok(f"chmod +x  scripts/{script.name}")

    hdr("Done")
    print(f"  Files created: {created}  Updated: {updated}")
    print()
    hdr(f"DEPLOY TO {SERVER_IP} -- 3 steps")
    print()
    print("  Step 1 -- Server setup (run ONCE):")
    print(f"    scp scripts/server_setup.sh {SERVER_SSH}:~/")
    print(f"    ssh {SERVER_SSH} 'bash ~/server_setup.sh'")
    print()
    print("  Step 2 -- Deploy from laptop:")
    print("    bash scripts/server_deploy.sh")
    print()
    print(f"  Step 3 -- Visit: http://{SERVER_IP}")
    print()
    print("  After pointing a domain:")
    print(f"    ssh {SERVER_SSH}")
    print("    sudo certbot --nginx -d yourdomain.com")
    print()
    print("  Full guide: cat HETZNER_DEPLOY.md")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Hetzner deployment files")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            import sys; sys.exit(0)
    build(root)
