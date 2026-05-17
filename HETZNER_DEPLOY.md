# NHMT-EA Hetzner Server Deployment Guide

**Server:** 178.105.16.51 (Ubuntu 24.04.4 LTS)
**User:** ymersha

---

## Step 1 -- Server setup (run ONCE)

Copy and run the setup script on the server:

```bash
# From your laptop:
scp scripts/server_setup.sh ymersha@178.105.16.51:~/
ssh ymersha@178.105.16.51 "bash ~/server_setup.sh"
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
| Frontend | http://178.105.16.51 |
| Backend  | http://178.105.16.51/api |
| API docs | http://178.105.16.51/api/docs |

---

## Step 3 -- Add a domain + HTTPS (recommended)

1. Point your domain A record to `178.105.16.51` in your DNS provider
2. Wait 5-60 minutes for DNS propagation
3. On the server, get a free SSL certificate:

```bash
ssh ymersha@178.105.16.51
sudo nano /etc/nginx/sites-available/net-ea
# Change: server_name 178.105.16.51 _;
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
ssh ymersha@178.105.16.51 "bash /opt/net-ea/scripts/server_update.sh"
```

---

## Server management commands

All run from your laptop:

```bash
# Check status
ssh ymersha@178.105.16.51 "cd /opt/net-ea && bash scripts/podman_status.sh"

# Follow backend logs
ssh ymersha@178.105.16.51 "cd /opt/net-ea && bash scripts/podman_logs.sh backend"

# Follow frontend logs
ssh ymersha@178.105.16.51 "cd /opt/net-ea && bash scripts/podman_logs.sh frontend"

# Restart containers
ssh ymersha@178.105.16.51 "cd /opt/net-ea && bash scripts/podman_stop.sh && bash scripts/podman_run.sh"

# SSH into backend container (debugging)
ssh ymersha@178.105.16.51 "podman exec -it net-ea-backend bash"

# View subscription data (stored in volume)
ssh ymersha@178.105.16.51 "podman exec net-ea-backend cat /app/data/subscriptions.json"

# Copy subscription data to laptop
ssh ymersha@178.105.16.51 "podman exec net-ea-backend cat /app/data/subscriptions.json" > subscriptions.json
```

---

## Auto-start on server reboot (Quadlet / systemd)

```bash
ssh ymersha@178.105.16.51
mkdir -p ~/.config/containers/systemd
cp /opt/net-ea/podman/quadlet/* ~/.config/containers/systemd/

# Create env file for backend
mkdir -p ~/.config/net-ea
cp /opt/net-ea/.env ~/.config/net-ea/backend.env

systemctl --user daemon-reload
systemctl --user enable --now net-ea.service

# Verify it started
systemctl --user status net-ea.service

# Enable lingering so service runs even when you're not logged in
loginctl enable-linger ymersha
```

Now NHMT-EA restarts automatically on server reboot.

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
ssh ymersha@178.105.16.51 "podman ps -a"
ssh ymersha@178.105.16.51 "podman logs net-ea-backend"
```

**Nginx not proxying correctly:**
```bash
ssh ymersha@178.105.16.51 "sudo nginx -t"
ssh ymersha@178.105.16.51 "sudo cat /var/log/nginx/net-ea-error.log"
```

**Port 3000/8000 not accessible:**
```bash
ssh ymersha@178.105.16.51 "sudo ufw status"
ssh ymersha@178.105.16.51 "podman ps"  # verify containers running
```

**Images not loading on server:**
```bash
ssh ymersha@178.105.16.51 "podman images"  # check images are present
```

---

*NHMT-EA v3.0 -- Yonas Mersha -- Y.Mersha@cgiar.org -- ILRI*
