# NHMT-EA Podman Deployment Guide

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

Quadlet integrates containers with systemd so NHMT-EA starts automatically
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

*NHMT-EA v3.0 -- Yonas Mersha -- Y.Mersha@cgiar.org -- ILRI*
