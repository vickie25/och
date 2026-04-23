import argparse
import datetime as dt
import json
import os
import re
import socket
from pathlib import Path

import paramiko


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
    return {"cmd": cmd, "exit_status": exit_status, "stdout": out, "stderr": err}


def run_sudo_sh(c: paramiko.SSHClient, sudo_password: str, sh_cmd: str, timeout: int) -> dict:
    safe = sh_cmd.replace('"', '\\"')
    cmd = f'printf "{sudo_password}\\n" | sudo -S -p "" sh -c "{safe}"'
    return run_cmd(c, cmd, timeout=timeout)


def write_bundle(out_dir: Path, results: list[dict]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    rollup = []
    for r in results:
        rollup.append(f"$ {r['cmd']}")
        rollup.append(f"exit_status={r['exit_status']}")
        if r.get("stdout"):
            rollup.append("---- stdout ----")
            rollup.append(r["stdout"].rstrip())
        if r.get("stderr"):
            rollup.append("---- stderr ----")
            rollup.append(r["stderr"].rstrip())
        rollup.append("")
    (out_dir / "rollup.txt").write_text("\n".join(rollup), encoding="utf-8")


SQL_CHECK_PY = r"""
from django.db import connection

def q(sql):
    with connection.cursor() as cur:
        cur.execute(sql)
        try:
            return cur.fetchall()
        except Exception:
            return []

print("to_regclass django_migrations:", q("select to_regclass('public.django_migrations')")[0][0])
print("to_regclass django_session:", q("select to_regclass('public.django_session')")[0][0])
print("to_regclass organizations:", q("select to_regclass('public.organizations')")[0][0])

try:
    print("django_migrations_count:", q("select count(*) from django_migrations")[0][0])
    print("latest_migrations:", q("select app, name from django_migrations order by applied desc limit 30"))
except Exception as e:
    print("django_migrations_query_error:", type(e).__name__, e)
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Check remote Django migration state vs DB tables.")
    ap.add_argument("--host", default=os.environ.get("OCH_SSH_HOST", "69.30.235.220"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("OCH_SSH_PORT", "22")))
    ap.add_argument("--username", default=os.environ.get("OCH_SSH_USER", "administrator"))
    ap.add_argument("--password", default=os.environ.get("OCH_SSH_PASSWORD", ""))
    ap.add_argument("--sudo-password", default=os.environ.get("OCH_SUDO_PASSWORD", ""))
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--out", default=str(Path("server_migration_state") / _now_tag()))
    args = ap.parse_args()

    if not args.password:
        print("Missing SSH password.")
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
        return 3

    try:
        results.append(run_sudo_sh(c, args.sudo_password, "docker ps -a --format 'table {{.Names}}\t{{.Status}}' 2>&1 || true", timeout=args.timeout))
        cmd = f"docker exec hub_prod_django python - <<'PY'\n{SQL_CHECK_PY}\nPY"
        results.append(run_sudo_sh(c, args.sudo_password, cmd + " 2>&1 || true", timeout=max(args.timeout, 90)))
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

