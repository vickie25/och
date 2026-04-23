import argparse
import datetime as dt
import json
import os
import re
import socket
from pathlib import Path

import paramiko


SENSITIVE_PATTERNS = [
    (re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*([^\s\"']+)"), r"\1=<redacted>"),
    (re.compile(r"(?i)\b(AWS|GCP|GOOGLE|OPENAI|STRIPE|DJANGO|JWT|POSTGRES|REDIS).*?(KEY|SECRET|TOKEN)\b\s*=\s*([^\s]+)"), r"<redacted_env>"),
]


def _sanitize(text: str) -> str:
    if not text:
        return text
    out = text
    for rx, repl in SENSITIVE_PATTERNS:
        out = rx.sub(repl, out)
    return out


def _now_tag() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def ssh_connect(host: str, username: str, password: str, port: int, timeout: int) -> paramiko.SSHClient:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(
        hostname=host,
        port=port,
        username=username,
        password=password,
        timeout=timeout,
        banner_timeout=timeout,
        auth_timeout=timeout,
    )
    return c


def run_cmd(c: paramiko.SSHClient, cmd: str, timeout: int) -> dict:
    stdin, stdout, stderr = c.exec_command(cmd, get_pty=False, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="ignore")
    err = stderr.read().decode("utf-8", errors="ignore")
    exit_status = stdout.channel.recv_exit_status()
    return {
        "cmd": cmd,
        "exit_status": exit_status,
        "stdout": _sanitize(out),
        "stderr": _sanitize(err),
    }


def run_sudo_sh(c: paramiko.SSHClient, sudo_password: str, sh_cmd: str, timeout: int) -> dict:
    safe = sh_cmd.replace('"', '\\"')
    cmd = f'printf "{sudo_password}\\n" | sudo -S -p "" sh -c "{safe}"'
    return run_cmd(c, cmd, timeout=timeout)


def write_bundle(out_dir: Path, results: list[dict]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    rollup_lines: list[str] = []
    for r in results:
        rollup_lines.append(f"$ {r['cmd']}")
        rollup_lines.append(f"exit_status={r['exit_status']}")
        if r.get("stdout"):
            rollup_lines.append("---- stdout ----")
            rollup_lines.append(r["stdout"].rstrip())
        if r.get("stderr"):
            rollup_lines.append("---- stderr ----")
            rollup_lines.append(r["stderr"].rstrip())
        rollup_lines.append("")
    (out_dir / "rollup.txt").write_text("\n".join(rollup_lines), encoding="utf-8")


ENV_AUDIT_PY = r"""
import json
import os
from pathlib import Path

def parse_env(p: str):
    path = Path(p)
    out = {"path": p, "exists": path.exists(), "keys": {}, "blank_keys": [], "total_keys": 0}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if not k:
            continue
        out["keys"][k] = bool(v)
    out["total_keys"] = len(out["keys"])
    out["blank_keys"] = sorted([k for k, has_v in out["keys"].items() if not has_v])
    return out

print(json.dumps({
    "compose_root_env": parse_env("/var/www/och/.env"),
    "django_env": parse_env("/var/www/och/backend/django_app/.env"),
}, indent=2))
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Deep remote audit: env keys, health, DB, migrations.")
    ap.add_argument("--host", default=os.environ.get("OCH_SSH_HOST", "69.30.235.220"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("OCH_SSH_PORT", "22")))
    ap.add_argument("--username", default=os.environ.get("OCH_SSH_USER", "administrator"))
    ap.add_argument("--password", default=os.environ.get("OCH_SSH_PASSWORD", ""))
    ap.add_argument("--sudo-password", default=os.environ.get("OCH_SUDO_PASSWORD", ""))
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--remote-root", default="/var/www/och")
    ap.add_argument("--out", default=str(Path("server_audit") / _now_tag()))
    args = ap.parse_args()

    if not args.password:
        print("Missing SSH password. Provide --password or set OCH_SSH_PASSWORD.")
        return 2
    if not args.sudo_password:
        args.sudo_password = args.password

    out_dir = Path(args.out).resolve()
    results: list[dict] = []

    try:
        c = ssh_connect(args.host, args.username, args.password, args.port, timeout=args.timeout)
    except (paramiko.AuthenticationException, paramiko.SSHException, socket.timeout, OSError) as e:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "connect_error.txt").write_text(str(e), encoding="utf-8")
        print(f"SSH connect failed: {e}")
        print(f"Wrote: {out_dir / 'connect_error.txt'}")
        return 3

    try:
        # Identify + basic resources
        results.append(run_cmd(c, "whoami && hostname && uptime", timeout=args.timeout))
        results.append(run_cmd(c, "df -h", timeout=args.timeout))
        results.append(run_cmd(c, "free -m || true", timeout=args.timeout))

        # Env audit (keys only; values never printed)
        env_cmd = f"python3 - <<'PY'\n{ENV_AUDIT_PY}\nPY"
        results.append(run_sudo_sh(c, args.sudo_password, env_cmd, timeout=max(args.timeout, 60)))

        # Compose + container health
        results.append(run_sudo_sh(c, args.sudo_password, "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, f"cd {args.remote_root} && (docker compose ps || docker-compose ps) || true", timeout=args.timeout))

        # Service endpoints from host (through published ports / localhost)
        results.append(run_sudo_sh(c, args.sudo_password, "curl -fsS -m 8 http://127.0.0.1/health 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "curl -fsS -m 8 http://127.0.0.1/api/v1/health/ 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "curl -fsS -m 8 http://127.0.0.1:8001/health 2>&1 || true", timeout=args.timeout))

        # Internal network checks from within containers (best effort)
        results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_nextjs node -e \"require('http').get(process.env.DJANGO_INTERNAL_URL||'http://django:8000/api/v1/health/', r=>{console.log('status',r.statusCode); process.exit(r.statusCode>=400?1:0)}).on('error',e=>{console.error(e.message); process.exit(2)})\" 2>&1 || true", timeout=max(args.timeout, 40)))
        results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_django python -c \"import socket; print(socket.gethostbyname('redis'))\" 2>&1 || true", timeout=args.timeout))

        # Django migrations + DB connectivity
        results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_django python manage.py migrate --check 2>&1 || true", timeout=max(args.timeout, 90)))
        results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_django python manage.py showmigrations --plan 2>&1 | tail -n 200 || true", timeout=max(args.timeout, 90)))

        # Postgres relational: readiness + table sample
        results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_postgres pg_isready -U postgres 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"select count(*) as tables from information_schema.tables where table_schema='public';\" 2>&1 || true", timeout=max(args.timeout, 60)))
        results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"select tablename from pg_tables where schemaname='public' order by tablename limit 40;\" 2>&1 || true", timeout=max(args.timeout, 60)))

        # Postgres vector: readiness + table sample
        results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_vector_db pg_isready -U postgres 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_vector_db psql -U postgres -d ongozacyberhub_vector -c \"select count(*) as tables from information_schema.tables where table_schema='public';\" 2>&1 || true", timeout=max(args.timeout, 60)))
        results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_vector_db psql -U postgres -d ongozacyberhub_vector -c \"select tablename from pg_tables where schemaname='public' order by tablename limit 40;\" 2>&1 || true", timeout=max(args.timeout, 60)))

    finally:
        try:
            c.close()
        except Exception:
            pass

    write_bundle(out_dir, results)
    print(f"Done. Wrote: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

