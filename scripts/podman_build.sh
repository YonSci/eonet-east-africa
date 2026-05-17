#!/bin/sh
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
podman build \
  -f "$ROOT/podman/Containerfile.backend" \
  -t localhost/nhmt-ea-backend:latest \
  "$ROOT"
echo "  Backend built: localhost/nhmt-ea-backend:latest"
echo ""

echo "[2/2] Building frontend image..."
podman build \
  -f "$ROOT/podman/Containerfile.frontend" \
  -t localhost/nhmt-ea-frontend:latest \
  "$ROOT"
echo "  Frontend built: localhost/nhmt-ea-frontend:latest"
echo ""

echo "Images:"
podman images | grep nhmt-ea || true
echo ""
echo "Next: sh scripts/podman_run.sh"
echo ""
