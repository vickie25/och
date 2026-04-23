# 🚨 NGINX SSL FIX GUIDE — `ERR_CONNECTION_REFUSED` on cybochengine.africa

**Created:** 2026-04-19  
**Last Verified:** 2026-04-19  
**Fix Time:** ~2 minutes  
**Server:** `69.30.235.220` (user: `administrator`) — **do not store SSH passwords in this repo**; use your team vault and GitHub Actions secrets (`SSH_PASSWORD`).

---

## The Problem

`https://cybochengine.africa` returns `ERR_CONNECTION_REFUSED` in the browser. The site appears completely dead. HTTP on port 80 may still work, but HTTPS on port 443 refuses all connections.

---

## Why This Happens

The Nginx Docker container reads its config from a **specific directory** that is NOT the obvious one:

| Directory on Host | Purpose | Mounted into Container? |
|---|---|---|
| `/var/www/och/nginx/conf.d/` | ❌ Decoy — looks correct but is **NOT used** | **NO** |
| `/var/www/och/nginx/conf.d-local/` | ✅ The **real** config directory | **YES** → maps to `/etc/nginx/conf.d/` |

The `conf.d-local/` directory only has an HTTP-only `default.conf` (port 80). Every time the nginx container is recreated (`docker-compose up`, `docker-compose restart`, etc.), the container boots with **no SSL config**, so port 443 serves nothing → `ERR_CONNECTION_REFUSED`.

### Root Cause in docker-compose.yml

The volume mount in docker-compose.yml binds `conf.d-local` instead of `conf.d`:
```yaml
nginx:
  volumes:
    - ./nginx/conf.d-local:/etc/nginx/conf.d:ro   # <-- THIS is what nginx reads
    - /etc/letsencrypt:/etc/letsencrypt:ro
```

---

## Quick Fix (2 Minutes)

### Step 1: SSH into the server
```bash
ssh administrator@69.30.235.220
# Password: Ongoza@#1
```

### Step 2: Check if the SSL config is missing
```bash
ls -la /var/www/och/nginx/conf.d-local/
```
If you only see `default.conf` (HTTP-only) and no `ssl.conf`, that's the problem.

### Step 3: Copy the SSL config into the correct directory
```bash
sudo cp /var/www/och/nginx/conf.d/local.conf /var/www/och/nginx/conf.d-local/ssl.conf
```

> **Note:** If `local.conf` doesn't exist in `conf.d/`, use the SSL config template at the bottom of this document instead.

### Step 4: Test and reload nginx
```bash
sudo docker exec hub_prod_nginx nginx -t
sudo docker exec hub_prod_nginx nginx -s reload
```

You should see:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

(A deprecation warning about `http2` is harmless — ignore it.)

### Step 5: Verify HTTPS is back
```bash
curl -I -k https://cybochengine.africa
```

Expected output:
```
HTTP/2 200
server: nginx/1.30.0
...
```

**Done!** The site is back up.

---

## Verification Checklist

After applying the fix, verify all services:

```bash
# 1. HTTPS landing page
curl -I -k https://cybochengine.africa
# Expected: HTTP/2 200

# 2. Django API health
curl -s -k https://cybochengine.africa/api/v1/health/
# Expected: {"status": "healthy", "service": "django", ...}

# 3. FastAPI AI health
curl -s -k https://cybochengine.africa/ai/health
# Expected: {"status":"healthy","service":"fastapi-ai","version":"v1"}

# 4. All containers running
sudo docker ps
# Expected: hub_prod_nginx, hub_prod_django, hub_prod_fastapi, hub_prod_nextjs, hub_prod_postgres, hub_prod_redis — all "Up" and "(healthy)"
```

---

## Permanent Fix (Do This When You Have Time)

To prevent this from ever happening again, update `docker-compose.yml` to mount the correct directory:

**Option A: Change the volume mount** (recommended)
```yaml
# In docker-compose.yml, change the nginx volumes from:
- ./nginx/conf.d-local:/etc/nginx/conf.d:ro
# To:
- ./nginx/conf.d:/etc/nginx/conf.d:ro
```
Then ensure `/var/www/och/nginx/conf.d/` contains only ONE active SSL config (e.g., `local.conf`), not multiple competing ones.

**Option B: Bake SSL config into conf.d-local permanently**
```bash
# Just make sure ssl.conf stays in conf.d-local
sudo cp /var/www/och/nginx/conf.d/local.conf /var/www/och/nginx/conf.d-local/ssl.conf
```
This survives nginx restarts/reloads, but will be lost if the container is fully recreated with a fresh volume.

---

## Diagnostic Commands

If the quick fix doesn't work, use these to investigate:

```bash
# What directory is nginx ACTUALLY reading from?
sudo docker inspect hub_prod_nginx --format '{{json .Mounts}}' | python3 -m json.tool

# What configs does nginx see inside the container?
sudo docker exec hub_prod_nginx ls -la /etc/nginx/conf.d/

# What ports is nginx listening on inside the container?
sudo docker exec hub_prod_nginx nginx -T 2>&1 | grep 'listen'

# Is port 443 mapped from host to container?
sudo docker port hub_prod_nginx

# Are SSL certs accessible inside the container?
sudo docker exec hub_prod_nginx ls -la /etc/letsencrypt/live/cybochengine.africa/

# Nginx error log
sudo docker logs hub_prod_nginx --tail=30

# Is anything else blocking port 443?
sudo netstat -tulpn | grep 443
```

---

## SSL Config Template

If `/var/www/och/nginx/conf.d/local.conf` is missing, create the SSL config manually:

```nginx
# /var/www/och/nginx/conf.d-local/ssl.conf

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name cybochengine.africa www.cybochengine.africa;

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name cybochengine.africa www.cybochengine.africa;

    ssl_certificate /etc/letsencrypt/live/cybochengine.africa/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cybochengine.africa/privkey.pem;

    client_header_buffer_size 16k;
    large_client_header_buffers 4 32k;

    set $forwarded_proto $scheme;

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Frontend (Next.js)
    location / {
        proxy_pass http://nextjs:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $forwarded_proto;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Django API
    location /api/ {
        proxy_pass http://django:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $forwarded_proto;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
        client_max_body_size 10M;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://django:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $forwarded_proto;
    }

    # FastAPI AI services
    location /ai/ {
        proxy_pass http://fastapi:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $forwarded_proto;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Django static files
    location /static/ {
        proxy_pass http://django:8000;
        proxy_set_header Host $host;
        proxy_cache_valid 200 60m;
        add_header Cache-Control "public, max-age=3600";
    }

    # Next.js static assets
    location /_next/static {
        proxy_pass http://nextjs:3000;
        proxy_cache_valid 200 60m;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## History of Occurrences

| Date | Trigger | Fix Applied | Time to Resolve |
|------|---------|-------------|-----------------|
| 2026-04-18 | Unknown (container recreation?) | SSL config restored | ~30 min (first discovery) |
| 2026-04-19 | Ghost crash during lunch break | Copied `local.conf` → `conf.d-local/ssl.conf` | ~15 min (with diagnosis) |

---

**Remember:** The trap is editing files in `conf.d/` — nginx doesn't read those. Always edit `conf.d-local/`.
