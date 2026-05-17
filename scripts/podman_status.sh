#!/bin/sh
# NHMT-EA health check
echo ""
echo "=== NHMT-EA Status ==="
echo ""

echo "Containers:"
podman ps --filter "name=nhmt-ea" \
  --format "  {{.Names}}  {{.Status}}  {{.Ports}}" 2>/dev/null || \
  podman ps | grep nhmt-ea || echo "  (none running)"

echo ""
echo "Images:"
podman images | grep nhmt-ea || echo "  (none built yet)"

echo ""
echo "Volume:"
podman volume inspect net-ea-data \
  --format "  net-ea-data  {{.Mountpoint}}" 2>/dev/null || echo "  (not created)"

echo ""
echo "Health:"
printf "  Backend  : "
wget -qO- http://localhost:8000/ 2>/dev/null | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('OK --', d.get('service','?'))" \
  2>/dev/null || echo "unreachable (start with: sh scripts/podman_run.sh)"

printf "  Frontend : "
wget -qO- http://localhost:3000/favicon.svg >/dev/null 2>&1 && echo "OK" || echo "unreachable"
echo ""
