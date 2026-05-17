#!/bin/sh
# NHMT-EA log tailing
# Usage: sh scripts/podman_logs.sh [backend|frontend]
SERVICE="${1:-backend}"
echo ""
echo "=== NHMT-EA logs: nhmt-ea-$SERVICE (Ctrl+C to stop) ==="
echo ""
podman logs -f --tail=50 "nhmt-ea-$SERVICE"
