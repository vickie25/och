# Handoff: Auth/RBAC cookie fix + production deploy

Use this so another agent can finish **server deployment** and verify dashboards. **Do not commit secrets or passwords into this repo.**

---

## 1. Problem we were fixing

- Users with **non-student roles** (finance, director, mentor, admin, etc.) were often sent to the **student dashboard** after login.
- **Root cause:** Role cookies (`och_roles`, `och_primary_role`, `och_dashboard`) were sometimes **empty or wrong** because:
  - Browser login hits **Django** directly (`apiGateway` → `/auth/login`), not always the Next BFF `/api/auth/login`.
  - **`POST /api/auth/set-tokens`** (called after login/MFA) only derived roles from `user.roles` and did **not** fall back to Django’s **`primary_role`** or **`is_superuser`** when `user.roles` was empty.
- Middleware (`proxy.ts`) reads those cookies for redirects; empty roles → student path.

---

## 2. What we changed (code)

**Single source of truth:** `frontend/nextjs_app/lib/rbacFromAuthPayload.ts`

- `normalizeRoleName`, `extractNormalizedRoles`, `resolveNormalizedRoles` (uses `user`, optional `primary_role` hint, `is_superuser` → admin), `getPrimaryRole`, `getDashboardForRole`.

**Updated to use the same resolver + fallbacks:**

| File | Role |
|------|------|
| `frontend/nextjs_app/app/api/auth/set-tokens/route.ts` | Reads `primary_role` from JSON body; sets cookies when `user` and/or `primary_role` present. |
| `frontend/nextjs_app/app/api/auth/login/route.ts` | Same resolver; aligns `och_*` cookie flags with set-tokens (non-HttpOnly for client fallback). |
| `frontend/nextjs_app/app/api/auth/ssologin/route.ts` | Same resolver + optional `primary_role`; aligned cookies. |
| `frontend/nextjs_app/hooks/useAuth.ts` | Passes `primary_role` into `set-tokens` body after login and after `completeMFA`. |
| `frontend/nextjs_app/proxy.ts` | If `och_roles` parses empty but `och_primary_role` cookie exists, recover one role via `normalizeRoleName`. |

**Git:** These changes were pushed to **`main`** as commit **`91da525`** (`fix(auth): unify RBAC cookies with Django primary_role …`).

**Repo hygiene:** Plaintext SSH password was removed from `NGINX_SSL_FIX_GUIDE.md` (line 6); secrets belong in vault + GitHub Actions only.

**Helper scripts (optional, local/scratch):** `scratch/_start_bg_pull.py` and similar were experiments for remote deploy; not required for production if you follow §5 below.

---

## 3. What’s already done vs remaining

| Item | Status |
|------|--------|
| Code merged to `main` | Done (`91da525`). |
| GitHub Actions **build** (django / fastapi / nextjs images) | Succeeded when last run. |
| GitHub Actions **Deploy to Production** (SSH from GitHub → VPS) | **Failed:** missing `SSH_PASSWORD` (or SSH key) in repo/environment secrets — fix when someone has GitHub admin access. |
| **Git on server** (`/var/www/och`) | Was verified at **`91da525`** at least once; re-check with `git log -1` if unsure. |
| **Docker: Next (and optionally django/fastapi) images + `up -d`** | **Likely still required.** Next runs from **prebuilt image** (`ghcr.io/.../och-nextjs:latest`), not bind-mounted app source — **must `docker compose pull` + `up`** for the running containers to match CI images. |

---

## 4. Paystack / nginx (context only)

- Whitelist target used in prod: `https://cybochengine.africa/api/v1/paystack/webhook/` (Django registers `paystack/webhook/` under `api/v1/` in `api/urls.py`).
- Legacy path `/paystack/webhook/` may hit Next 404 on this host; keep Paystack dashboard URL aligned with `/api/v1/...` if that’s what nginx routes to Django.

---

## 5. Instructions: server deployment (for the next agent)

**Prerequisites:** SSH access to the production host, `sudo`, Docker, and repo at **`/var/www/och`** (adjust path if different).

### 5.1 Confirm Git matches GitHub `main`

```bash
cd /var/www/och
sudo git fetch origin
sudo git status -sb
sudo git log -1 --oneline
```

- Expect commit **`91da525`** (or newer on `main`).  
- If merge is blocked by **local changes**, either **stash** (`sudo git stash push -u`) or, if prod must mirror GitHub exactly, **`sudo git reset --hard origin/main`** (discards server-only edits).

### 5.2 Refresh containers (required for Next auth fix in production)

```bash
cd /var/www/och
sudo docker compose pull nextjs django fastapi
sudo docker compose up -d
sudo docker compose ps
```

If **`docker compose pull`** fails with **unauthorized** to GHCR, log the server into `ghcr.io` once (PAT with `read:packages`), or build Next on-server (heavy RAM; see `deploy/build-next-low-mem.sh` in repo).

### 5.3 Optional: overnight background pull (if interactive session might drop)

```bash
cd /var/www/och
nohup sudo bash -c 'docker compose pull nextjs django fastapi >> /tmp/och_docker_pull.log 2>&1 && docker compose up -d >> /tmp/och_docker_pull.log 2>&1 && echo DONE_UP >> /tmp/och_docker_pull.log' &
```

Next day: `tail -100 /tmp/och_docker_pull.log` and confirm **`DONE_UP`**.

### 5.4 Fix GitHub Actions deploy (when possible)

- Repo → **Settings → Secrets and variables → Actions** (and **Environment `production`** if used).  
- Add **`SSH_PASSWORD`** matching the deploy user, **or** switch `appleboy/ssh-action` to an **SSH private key** secret.  
- Re-run failed **Deploy to Production** workflow.

### 5.5 Verification (smoke)

- `curl -sS https://cybochengine.africa/api/v1/health/` → Django healthy.  
- Browser: log in as **finance / director / mentor / admin** (and MFA if enabled) → confirm **correct dashboard**, not always student.  
- DevTools → Application → Cookies: `och_roles` / `och_dashboard` should reflect role (when set-tokens/login ran).

---

## 6. Security reminder

- **Rotate** any SSH password that was ever pasted in chat or committed to markdown.  
- **Never** store production passwords in tracked files; use vault + CI secrets.

---

## 7. One-line summary for the next agent

**Implement RBAC cookie alignment in Next (`91da525` on `main`); CI images build OK; finish by pulling/updating Docker on the VPS (`docker compose pull` + `up -d`), fix GitHub `SSH_PASSWORD` for automated deploy, then smoke-test role dashboards.**
