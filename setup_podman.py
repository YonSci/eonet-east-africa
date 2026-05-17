"""
setup_podman.py
---------------
Replaces Docker deployment with Podman for NET-EA.

Key differences from Docker:
  - Podman is daemonless (runs as root-less user process)
  - Uses 'podman' and 'podman-compose' commands instead of 'docker'
  - Uses Quadlet (.container files) for systemd auto-start on Linux
  - No daemon process needed -- each container is its own process
  - Fully compatible with existing Dockerfile syntax
  - podman-compose is a drop-in replacement for docker-compose

Files created / updated:
  podman/                           (replaces docker/)
    Containerfile.backend           -- same as Dockerfile, Podman naming convention
    Containerfile.frontend          -- Nginx serving the built React app
    podman-compose.yml              -- podman-compose equivalent of docker-compose
    nginx.conf                      -- Nginx config for SPA routing
  podman/quadlet/                   -- systemd auto-start (Linux/RHEL/Fedora)
    net-ea-backend.container        -- backend systemd unit
    net-ea-frontend.container       -- frontend systemd unit
    net-ea-pod.pod                  -- pod definition
  scripts/
    podman_build.sh                 -- build both images
    podman_run.sh                   -- start containers
    podman_stop.sh                  -- stop containers
    podman_logs.sh                  -- tail logs
    podman_status.sh                -- health check
  PODMAN_DEPLOY.md                  -- full deployment guide

Run from the eonet-east-africa project root:
    python setup_podman.py
"""

import sys, argparse
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

FILES = {}

# =============================================================================
# Containerfile.backend  (identical syntax to Dockerfile -- Podman reads both)
# =============================================================================
FILES["podman/Containerfile.backend"] = """# NET-EA Backend -- FastAPI + uvicorn
# Build: podman build -f podman/Containerfile.backend -t net-ea-backend .
# Run:   podman run -d --name net-ea-backend -p 8000:8000 net-ea-backend

FROM docker.io/python:3.12-slim

LABEL maintainer="Yonas Mersha <Y.Mersha@cgiar.org>"
LABEL description="NET-EA Natural Event Tracker for East Africa -- Backend"
LABEL version="3.0.0"

WORKDIR /app

# Install dependencies first (layer cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY backend/ ./backend/
COPY data/    ./data/

# Copy env file (overridden at runtime by --env-file or -e flags)
COPY .env.example .env

# Create non-root user for rootless Podman
RUN useradd --no-create-home --shell /bin/false appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" \
  || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--log-level", "info"]
"""

# =============================================================================
# Containerfile.frontend  (Nginx serving the built Vite app)
# =============================================================================
FILES["podman/Containerfile.frontend"] = """# NET-EA Frontend -- Nginx serving Vite build
# Build: podman build -f podman/Containerfile.frontend -t net-ea-frontend .
# Run:   podman run -d --name net-ea-frontend -p 3000:80 net-ea-frontend

FROM docker.io/node:20-slim AS builder

LABEL stage="builder"
WORKDIR /build

# Install Node deps first (cached layer)
COPY frontend/package*.json ./
RUN npm ci --silent

# Build the Vite app
COPY frontend/ ./
ENV VITE_EONET_DIRECT=true
RUN npm run build

# ---- Production image: Nginx serves the built files ----
FROM docker.io/nginx:alpine

LABEL maintainer="Yonas Mersha <Y.Mersha@cgiar.org>"
LABEL description="NET-EA Natural Event Tracker -- Frontend"
LABEL version="3.0.0"

# Copy built app
COPY --from=builder /build/dist /usr/share/nginx/html

# Copy custom Nginx config (SPA fallback routing)
COPY podman/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost/favicon.svg || exit 1

CMD ["nginx", "-g", "daemon off;"]
"""

# =============================================================================
# nginx.conf  -- SPA routing so React Router works
# =============================================================================
FILES["podman/nginx.conf"] = """server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml image/svg+xml;
    gzip_min_length 1024;

    # Cache static assets aggressively (Vite adds content hashes)
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA fallback -- send all routes to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy (optional -- when running both containers)
    location /events {
        proxy_pass http://net-ea-backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 10s;
        proxy_read_timeout 30s;
    }
    location /summary { proxy_pass http://net-ea-backend:8000; }
    location /status  { proxy_pass http://net-ea-backend:8000; }
    location /alerts  { proxy_pass http://net-ea-backend:8000; }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
"""

# =============================================================================
# podman-compose.yml  (compatible with podman-compose and docker-compose v3)
# =============================================================================
FILES["podman/podman-compose.yml"] = """# NET-EA Podman Compose
# Usage:
#   podman-compose -f podman/podman-compose.yml up -d
#   podman-compose -f podman/podman-compose.yml down
#   podman-compose -f podman/podman-compose.yml logs -f

version: "3.8"

services:

  backend:
    build:
      context: ..
      dockerfile: podman/Containerfile.backend
    image: localhost/net-ea-backend:latest
    container_name: net-ea-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - ../.env
    environment:
      - BACKEND_HOST=0.0.0.0
      - BACKEND_PORT=8000
    volumes:
      # Persist subscription data outside the container
      - net-ea-data:/app/data
    healthcheck:
      test: ["CMD", "python", "-c",
             "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s

  frontend:
    build:
      context: ..
      dockerfile: podman/Containerfile.frontend
    image: localhost/net-ea-frontend:latest
    container_name: net-ea-frontend
    restart: unless-stopped
    ports:
      - "3000:80"
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost/favicon.svg"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

volumes:
  net-ea-data:
    name: net-ea-data
"""

# =============================================================================
# Quadlet files -- systemd auto-start (Linux: RHEL 9, Fedora 35+, Ubuntu 22+)
# =============================================================================
FILES["podman/quadlet/net-ea.pod"] = """# NET-EA Podman Pod definition (Quadlet)
# Place in: ~/.config/containers/systemd/
# Then run: systemctl --user daemon-reload
#           systemctl --user start net-ea.service

[Unit]
Description=NET-EA Natural Event Tracker for East Africa
Documentation=https://github.com/YOUR_USERNAME/eonet-east-africa

[Pod]
PublishPort=3000:80
PublishPort=8000:8000

[Service]
Restart=on-failure

[Install]
WantedBy=default.target
"""

FILES["podman/quadlet/net-ea-backend.container"] = """# NET-EA Backend container (Quadlet)
# Place in: ~/.config/containers/systemd/
# Auto-started by net-ea.pod

[Unit]
Description=NET-EA Backend (FastAPI)
After=network.target

[Container]
Image=localhost/net-ea-backend:latest
ContainerName=net-ea-backend
Pod=net-ea.pod
EnvironmentFile=%h/.config/net-ea/backend.env
Volume=net-ea-data:/app/data:Z
HealthCmd=python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"
HealthInterval=30s
HealthTimeout=10s
HealthRetries=3
HealthStartPeriod=15s

[Service]
Restart=on-failure
TimeoutStartSec=60

[Install]
WantedBy=net-ea.service
"""

FILES["podman/quadlet/net-ea-frontend.container"] = """# NET-EA Frontend container (Quadlet)
# Place in: ~/.config/containers/systemd/

[Unit]
Description=NET-EA Frontend (Nginx + React)
After=net-ea-backend.service

[Container]
Image=localhost/net-ea-frontend:latest
ContainerName=net-ea-frontend
Pod=net-ea.pod
HealthCmd=wget -qO- http://localhost/favicon.svg
HealthInterval=30s
HealthTimeout=5s
HealthRetries=3
HealthStartPeriod=10s

[Service]
Restart=on-failure
TimeoutStartSec=30

[Install]
WantedBy=net-ea.service
"""

# =============================================================================
# Shell scripts
# =============================================================================
FILES["scripts/podman_build.sh"] = """#!/bin/bash
# NET-EA Podman build script
# Usage: bash scripts/podman_build.sh
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo ""
echo "=== NET-EA Podman Build ==="
echo "Project root: $ROOT"
echo ""

# Build backend image
echo "[1/2] Building backend image..."
podman build \\
  -f "$ROOT/podman/Containerfile.backend" \\
  -t localhost/net-ea-backend:latest \\
  --label "build-date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \\
  "$ROOT"
echo "  Backend image built: localhost/net-ea-backend:latest"
echo ""

# Build frontend image
echo "[2/2] Building frontend image..."
podman build \\
  -f "$ROOT/podman/Containerfile.frontend" \\
  -t localhost/net-ea-frontend:latest \\
  --label "build-date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \\
  "$ROOT"
echo "  Frontend image built: localhost/net-ea-frontend:latest"
echo ""

echo "Images:"
podman images | grep net-ea
echo ""
echo "Next: bash scripts/podman_run.sh"
"""

FILES["scripts/podman_run.sh"] = """#!/bin/bash
# NET-EA Podman run script
# Usage: bash scripts/podman_run.sh
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "=== NET-EA Podman Start ==="
echo ""

# Create data volume if it doesn't exist
podman volume create net-ea-data 2>/dev/null || true
echo "  Volume: net-ea-data ready"

# Stop existing containers if running
podman stop net-ea-backend  2>/dev/null || true
podman stop net-ea-frontend 2>/dev/null || true
podman rm   net-ea-backend  2>/dev/null || true
podman rm   net-ea-frontend 2>/dev/null || true

# Create a pod so containers share network namespace
podman pod create \\
  --name net-ea \\
  --publish 8000:8000 \\
  --publish 3000:80 \\
  2>/dev/null || podman pod start net-ea 2>/dev/null || true

# Start backend
echo "[1/2] Starting backend..."
podman run -d \\
  --name net-ea-backend \\
  --pod net-ea \\
  --env-file "$ROOT/.env" \\
  --volume net-ea-data:/app/data:Z \\
  --restart unless-stopped \\
  localhost/net-ea-backend:latest
echo "  Backend started"

# Wait for backend health check
echo "  Waiting for backend to be healthy..."
for i in $(seq 1 20); do
  if podman healthcheck run net-ea-backend 2>/dev/null | grep -q healthy 2>/dev/null; then
    echo "  Backend healthy"
    break
  fi
  sleep 2
  echo -n "."
done
echo ""

# Start frontend
echo "[2/2] Starting frontend..."
podman run -d \\
  --name net-ea-frontend \\
  --pod net-ea \\
  --restart unless-stopped \\
  localhost/net-ea-frontend:latest
echo "  Frontend started"

echo ""
echo "=== NET-EA is running ==="
echo ""
echo "  Frontend : http://localhost:3000"
echo "  Backend  : http://localhost:8000"
echo "  API docs : http://localhost:8000/docs"
echo ""
echo "  Logs     : bash scripts/podman_logs.sh"
echo "  Status   : bash scripts/podman_status.sh"
echo "  Stop     : bash scripts/podman_stop.sh"
echo ""
"""

FILES["scripts/podman_stop.sh"] = """#!/bin/bash
# NET-EA Podman stop script
echo ""
echo "=== Stopping NET-EA ==="
podman stop net-ea-frontend 2>/dev/null && echo "  Frontend stopped" || true
podman stop net-ea-backend  2>/dev/null && echo "  Backend stopped"  || true
podman pod stop net-ea      2>/dev/null && echo "  Pod stopped"      || true
echo "Done"
echo ""
echo "To remove containers: podman rm net-ea-backend net-ea-frontend"
echo "To remove images:     podman rmi net-ea-backend net-ea-frontend"
echo "To remove data volume: podman volume rm net-ea-data"
echo ""
"""

FILES["scripts/podman_logs.sh"] = """#!/bin/bash
# NET-EA log tailing
# Usage: bash scripts/podman_logs.sh [backend|frontend]
SERVICE="${1:-backend}"
echo ""
echo "=== NET-EA logs: net-ea-$SERVICE (Ctrl+C to stop) ==="
echo ""
podman logs -f --tail=50 "net-ea-$SERVICE"
"""

FILES["scripts/podman_status.sh"] = """#!/bin/bash
# NET-EA health check
echo ""
echo "=== NET-EA Status ==="
echo ""
echo "Containers:"
podman ps --filter "name=net-ea" --format "  {{.Names}}  {{.Status}}  {{.Ports}}" 2>/dev/null
echo ""
echo "Images:"
podman images --filter "reference=localhost/net-ea*" \\
  --format "  {{.Repository}}:{{.Tag}}  {{.Size}}" 2>/dev/null
echo ""
echo "Volume:"
podman volume inspect net-ea-data \\
  --format "  net-ea-data  Mountpoint: {{.Mountpoint}}" 2>/dev/null || echo "  not created"
echo ""
echo "Health:"
echo -n "  Backend  : "
curl -sf http://localhost:8000/ | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK --', d.get('service','?'))" 2>/dev/null || echo "unreachable"
echo -n "  Frontend : "
curl -sf http://localhost:3000/favicon.svg > /dev/null && echo "OK" || echo "unreachable"
echo ""
"""

# =============================================================================
# .podmanignore -- prevents build context bloat
# =============================================================================
FILES["podman/.podmanignore"] = """.git/
.venv/
node_modules/
frontend/dist/
frontend/.vite/
data/*.json
data/*.geojson
__pycache__/
*.pyc
.env
*.log
.DS_Store
"""

# =============================================================================
# PODMAN_DEPLOY.md -- complete deployment guide
# =============================================================================
FILES["PODMAN_DEPLOY.md"] = """# NET-EA Podman Deployment Guide

## Why Podman instead of Docker?

| Feature | Docker | Podman |
|---|---|---|
| Daemon | Requires dockerd running as root | Daemonless -- no background service |
| Root | Default: root daemon | Rootless by default -- runs as your user |
| Compatibility | - | Full Docker CLI compatibility |
| RHEL / Fedora | Not included | Built-in on RHEL 8+, Fedora 35+ |
| Systemd | External tools needed | Native Quadlet support |
| Security | Daemon is attack surface | No daemon = smaller attack surface |
| Commands | docker / docker-compose | podman / podman-compose (drop-in) |

---

## Prerequisites

### Install Podman

```bash
# Ubuntu 22.04+
sudo apt update && sudo apt install -y podman

# RHEL / Rocky Linux / AlmaLinux 8+
sudo dnf install -y podman

# Fedora
sudo dnf install -y podman

# macOS (Homebrew)
brew install podman
podman machine init
podman machine start

# Windows
# Download Podman Desktop from https://podman-desktop.io
```

### Install podman-compose

```bash
pip install podman-compose --break-system-packages
```

### Verify

```bash
podman --version      # should print 4.x or 5.x
podman-compose --version
```

---

## Option A -- Single commands (simplest)

```bash
# 1. Build images
bash scripts/podman_build.sh

# 2. Start containers
bash scripts/podman_run.sh

# 3. Open in browser
#    Frontend: http://localhost:3000
#    API docs: http://localhost:8000/docs
```

---

## Option B -- podman-compose (closest to docker-compose)

```bash
# Build and start everything
podman-compose -f podman/podman-compose.yml up -d --build

# Check status
podman-compose -f podman/podman-compose.yml ps

# Follow logs
podman-compose -f podman/podman-compose.yml logs -f

# Stop and remove
podman-compose -f podman/podman-compose.yml down
```

---

## Option C -- Quadlet (systemd auto-start on Linux)

Quadlet integrates containers with systemd so NET-EA starts automatically
on boot and restarts on failure, like any system service.

```bash
# 1. Build images first
bash scripts/podman_build.sh

# 2. Copy Quadlet files to your systemd user directory
mkdir -p ~/.config/containers/systemd
cp podman/quadlet/* ~/.config/containers/systemd/

# 3. Create the env file for the backend
mkdir -p ~/.config/net-ea
cp .env ~/.config/net-ea/backend.env

# 4. Reload systemd and start
systemctl --user daemon-reload
systemctl --user enable --now net-ea.service

# 5. Check status
systemctl --user status net-ea.service
journalctl --user -u net-ea -f
```

To stop:
```bash
systemctl --user stop net-ea.service
```

---

## Useful Podman commands

```bash
# List running containers
podman ps

# List all containers (including stopped)
podman ps -a

# View logs
podman logs -f net-ea-backend
podman logs -f net-ea-frontend

# Exec into a running container
podman exec -it net-ea-backend bash

# Copy files into/out of container
podman cp net-ea-backend:/app/data/subscriptions.json ./subscriptions.json

# Inspect container
podman inspect net-ea-backend

# Remove everything
podman stop net-ea-backend net-ea-frontend
podman rm   net-ea-backend net-ea-frontend
podman rmi  localhost/net-ea-backend localhost/net-ea-frontend
podman volume rm net-ea-data
podman pod rm net-ea

# Save image to file (for transfer to another server)
podman save localhost/net-ea-backend:latest | gzip > net-ea-backend.tar.gz
podman load < net-ea-backend.tar.gz
```

---

## Production deployment on a Linux server

```bash
# On your laptop -- build and export
podman build -f podman/Containerfile.backend -t net-ea-backend .
podman build -f podman/Containerfile.frontend -t net-ea-frontend .
podman save localhost/net-ea-backend:latest  | gzip > net-ea-backend.tar.gz
podman save localhost/net-ea-frontend:latest | gzip > net-ea-frontend.tar.gz

# On the server -- import and run
scp net-ea-*.tar.gz user@your-server:/opt/net-ea/
ssh user@your-server
cd /opt/net-ea
podman load < net-ea-backend.tar.gz
podman load < net-ea-frontend.tar.gz
bash scripts/podman_run.sh
```

---

## Troubleshooting

**Port already in use:**
```bash
podman ps                          # find what's running
podman stop net-ea-backend         # stop it
# or change port in podman_run.sh: --publish 8001:8000
```

**Permission denied on volume:**
```bash
# Add :Z label for SELinux (RHEL/Fedora)
podman run ... --volume net-ea-data:/app/data:Z ...
```

**Container exits immediately:**
```bash
podman logs net-ea-backend         # see the error
podman inspect net-ea-backend      # full container state
```

**podman-compose not found:**
```bash
pip install podman-compose --break-system-packages
# or:
pip3 install podman-compose
```

---

*NET-EA v3.0 -- Yonas Mersha -- Y.Mersha@cgiar.org -- ILRI*
"""

# =============================================================================
# Update .gitignore -- add podman-specific entries
# =============================================================================
GITIGNORE_APPEND = """
# Podman
podman/*.env
podman/quadlet/*.env
*.tar.gz
"""

# =============================================================================
# Builder
# =============================================================================
def build(root: Path):
    hdr(f"Setting up Podman deployment in: {root}")
    created = updated = 0

    # Create files
    for rel, content in FILES.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        (ow if existed else ok)(("update  " if existed else "create  ") + rel)
        if existed: updated += 1
        else: created += 1

    # Make shell scripts executable
    for script in (root / "scripts").glob("podman_*.sh"):
        script.chmod(script.stat().st_mode | 0o755)
        ok(f"chmod +x  scripts/{script.name}")

    # Update .gitignore
    gi = root / ".gitignore"
    if gi.exists():
        txt = gi.read_text(encoding="utf-8")
        if "Podman" not in txt:
            gi.write_text(txt.rstrip() + "\n" + GITIGNORE_APPEND, encoding="utf-8")
            ow("patch   .gitignore (Podman entries)")

    # Summary
    hdr("Done")
    print(f"  Files created : {created}")
    print(f"  Files updated : {updated}")
    print()
    print("  Deployment options:")
    print()
    print("  Option A -- Script-based (simplest):")
    print("    bash scripts/podman_build.sh")
    print("    bash scripts/podman_run.sh")
    print("    # Open: http://localhost:3000")
    print()
    print("  Option B -- podman-compose:")
    print("    pip install podman-compose --break-system-packages")
    print("    podman-compose -f podman/podman-compose.yml up -d --build")
    print()
    print("  Option C -- systemd auto-start (Linux):")
    print("    bash scripts/podman_build.sh")
    print("    cp podman/quadlet/* ~/.config/containers/systemd/")
    print("    systemctl --user daemon-reload")
    print("    systemctl --user enable --now net-ea.service")
    print()
    print("  Management commands:")
    print("    bash scripts/podman_status.sh  -- health check")
    print("    bash scripts/podman_logs.sh    -- tail backend logs")
    print("    bash scripts/podman_stop.sh    -- stop all containers")
    print()
    print("  Full guide: cat PODMAN_DEPLOY.md")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Set up Podman deployment for NET-EA")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)
