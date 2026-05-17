"""
setup_script_fix.py
-------------------
Fixes the "pipefail: invalid option" error.

Root cause: the server may have /bin/bash missing or symlinked to dash
(Debian/Ubuntu often symlink /bin/sh to dash, not bash).
Running 'bash scripts/podman_build.sh' should work, but 'sh' or
executing directly without bash will fail on bash-only options.

Fix: rewrite all shell scripts to be POSIX sh compatible (no bashisms)
AND add an explicit bash check at the top so the error is clear.
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
# podman_build.sh  --  POSIX sh compatible
# =============================================================================
FILES["scripts/podman_build.sh"] = """#!/bin/sh
# NHMT-EA Podman build script
# Usage:
#   bash scripts/podman_build.sh    (Linux / macOS)
#   sh   scripts/podman_build.sh    (also works)
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo ""
echo "=== NHMT-EA Podman Build ==="
echo "Project root: $ROOT"
echo ""

echo "[1/2] Building backend image..."
podman build \\
  -f "$ROOT/podman/Containerfile.backend" \\
  -t localhost/nhmt-ea-backend:latest \\
  "$ROOT"
echo "  Backend built: localhost/nhmt-ea-backend:latest"
echo ""

echo "[2/2] Building frontend image..."
podman build \\
  -f "$ROOT/podman/Containerfile.frontend" \\
  -t localhost/nhmt-ea-frontend:latest \\
  "$ROOT"
echo "  Frontend built: localhost/nhmt-ea-frontend:latest"
echo ""

echo "Images:"
podman images | grep nhmt-ea || true
echo ""
echo "Next: sh scripts/podman_run.sh"
echo ""
"""

# =============================================================================
# podman_run.sh  --  POSIX sh compatible
# =============================================================================
FILES["scripts/podman_run.sh"] = """#!/bin/sh
# NHMT-EA Podman run script
# Usage: sh scripts/podman_run.sh
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "=== NHMT-EA Podman Start ==="
echo ""

# Create data volume if needed
podman volume create net-ea-data 2>/dev/null || true
echo "  Volume: net-ea-data ready"

# Stop and remove existing containers
podman stop  nhmt-ea-backend  2>/dev/null || true
podman stop  nhmt-ea-frontend 2>/dev/null || true
podman rm    nhmt-ea-backend  2>/dev/null || true
podman rm    nhmt-ea-frontend 2>/dev/null || true

# Remove old pod if exists, recreate
podman pod rm nhmt-ea 2>/dev/null || true
podman pod create \\
  --name nhmt-ea \\
  --publish 8000:8000 \\
  --publish 3000:80

echo "[1/2] Starting backend..."
podman run -d \\
  --name nhmt-ea-backend \\
  --pod nhmt-ea \\
  --env-file "$ROOT/.env" \\
  --volume net-ea-data:/app/data:Z \\
  --restart unless-stopped \\
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
podman run -d \\
  --name nhmt-ea-frontend \\
  --pod nhmt-ea \\
  --restart unless-stopped \\
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
"""

# =============================================================================
# podman_stop.sh  --  POSIX sh compatible
# =============================================================================
FILES["scripts/podman_stop.sh"] = """#!/bin/sh
# NHMT-EA Podman stop script
echo ""
echo "=== Stopping NHMT-EA ==="
podman stop nhmt-ea-frontend 2>/dev/null && echo "  Frontend stopped" || true
podman stop nhmt-ea-backend  2>/dev/null && echo "  Backend stopped"  || true
podman pod stop nhmt-ea      2>/dev/null && echo "  Pod stopped"      || true
echo "Done"
echo ""
echo "To remove containers: podman rm nhmt-ea-backend nhmt-ea-frontend"
echo "To remove pod:        podman pod rm nhmt-ea"
echo "To remove images:     podman rmi localhost/nhmt-ea-backend localhost/nhmt-ea-frontend"
echo "To remove data:       podman volume rm net-ea-data"
echo ""
"""

# =============================================================================
# podman_logs.sh  --  POSIX sh compatible
# =============================================================================
FILES["scripts/podman_logs.sh"] = """#!/bin/sh
# NHMT-EA log tailing
# Usage: sh scripts/podman_logs.sh [backend|frontend]
SERVICE="${1:-backend}"
echo ""
echo "=== NHMT-EA logs: nhmt-ea-$SERVICE (Ctrl+C to stop) ==="
echo ""
podman logs -f --tail=50 "nhmt-ea-$SERVICE"
"""

# =============================================================================
# podman_status.sh  --  POSIX sh compatible
# =============================================================================
FILES["scripts/podman_status.sh"] = """#!/bin/sh
# NHMT-EA health check
echo ""
echo "=== NHMT-EA Status ==="
echo ""

echo "Containers:"
podman ps --filter "name=nhmt-ea" \\
  --format "  {{.Names}}  {{.Status}}  {{.Ports}}" 2>/dev/null || \\
  podman ps | grep nhmt-ea || echo "  (none running)"

echo ""
echo "Images:"
podman images | grep nhmt-ea || echo "  (none built yet)"

echo ""
echo "Volume:"
podman volume inspect net-ea-data \\
  --format "  net-ea-data  {{.Mountpoint}}" 2>/dev/null || echo "  (not created)"

echo ""
echo "Health:"
printf "  Backend  : "
wget -qO- http://localhost:8000/ 2>/dev/null | \\
  python3 -c "import sys,json; d=json.load(sys.stdin); print('OK --', d.get('service','?'))" \\
  2>/dev/null || echo "unreachable (start with: sh scripts/podman_run.sh)"

printf "  Frontend : "
wget -qO- http://localhost:3000/favicon.svg >/dev/null 2>&1 && echo "OK" || echo "unreachable"
echo ""
"""

# =============================================================================
# podman_build.sh for server  --  explicit bash on server
# =============================================================================
FILES["scripts/server_setup.sh"] = """#!/bin/sh
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
sudo pip3 install podman-compose --break-system-packages -q 2>/dev/null || \\
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
"""

# =============================================================================
# server_deploy.sh  --  sh compatible, uses explicit sh for sub-scripts
# =============================================================================
FILES["scripts/server_deploy.sh"] = """#!/bin/sh
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
podman build -f "$ROOT/podman/Containerfile.backend"  \\
  -t localhost/nhmt-ea-backend:latest  "$ROOT"
podman build -f "$ROOT/podman/Containerfile.frontend" \\
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
ssh "$SERVER" "podman load < /tmp/nhmt-ea-backend.tar.gz  && \\
               podman load < /tmp/nhmt-ea-frontend.tar.gz && \\
               rm -f /tmp/nhmt-ea-backend.tar.gz /tmp/nhmt-ea-frontend.tar.gz"
echo "  Images loaded"

echo "[5/5] Starting containers on server..."
ssh "$SERVER" "sh $REPO/scripts/podman_run.sh"

echo "  Setting up Nginx proxy..."
ssh "$SERVER" "sudo cp $REPO/podman/nginx-proxy.conf /etc/nginx/sites-available/nhmt-ea && \\
               sudo ln -sf /etc/nginx/sites-available/nhmt-ea \\
                           /etc/nginx/sites-enabled/nhmt-ea && \\
               sudo rm -f /etc/nginx/sites-enabled/default && \\
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
"""

# =============================================================================
# server_update.sh  --  sh compatible
# =============================================================================
FILES["scripts/server_update.sh"] = """#!/bin/sh
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
"""

# =============================================================================
# server_push_only.sh
# =============================================================================
FILES["scripts/server_push_only.sh"] = """#!/bin/sh
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
ssh "$SERVER" "podman load < /tmp/nhmt-ea-backend.tar.gz  && \\
               podman load < /tmp/nhmt-ea-frontend.tar.gz && \\
               rm -f /tmp/nhmt-ea-*.tar.gz && \\
               sh $REPO/scripts/podman_run.sh"

rm -f /tmp/nhmt-ea-backend.tar.gz /tmp/nhmt-ea-frontend.tar.gz
echo ""
echo "Done -- http://178.105.16.51"
echo ""
"""

# =============================================================================
# Builder
# =============================================================================
def build(root: Path):
    fe = root / "frontend"
    hdr(f"Fixing shell scripts (sh-compatible) in: {root}")
    created = updated = 0

    for rel, content in FILES.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        (ow if existed else ok)(("update  " if existed else "create  ") + rel)
        target.chmod(target.stat().st_mode | 0o755)
        if existed: updated += 1
        else: created += 1

    # Verify shebang and no bashisms
    print()
    issues = []
    for rel in FILES:
        p = root / rel
        if not p.exists(): continue
        lines = p.read_text().split("\n")
        shebang = lines[0] if lines else ""
        has_pipefail = any("pipefail" in l for l in lines)
        has_arrays   = any("=(" in l or "[@]" in l for l in lines)
        has_bashonly = any("[[" in l for l in lines)
        if has_pipefail or has_arrays or has_bashonly:
            issues.append(f"  WARN  {rel} -- bashism found")
        print(f"  OK  {rel}  shebang={shebang}")

    if issues:
        print()
        for i in issues: print(i)
    else:
        print()
        ok("All scripts are POSIX sh compatible -- no bashisms")

    hdr("Done")
    print(f"  Files created : {created}")
    print(f"  Files updated : {updated}")
    print()
    print("  Now run with sh instead of bash:")
    print("    sh scripts/podman_build.sh")
    print("    sh scripts/podman_run.sh")
    print()
    print("  Or install bash if missing:")
    print("    sudo apt install -y bash     # Ubuntu/Debian")
    print("    sudo dnf install -y bash     # RHEL/Fedora")
    print()
    print("  On the Hetzner server:")
    print("    sh scripts/server_setup.sh")
    print("    sh scripts/server_deploy.sh")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fix shell scripts for sh compatibility")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)
