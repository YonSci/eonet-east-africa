#!/bin/sh
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
