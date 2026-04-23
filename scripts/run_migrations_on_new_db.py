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


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Django migration checks (and optionally migrate) on VPS.")
    ap.add_argument("--host", default=os.environ.get("OCH_SSH_HOST", "69.30.235.220"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("OCH_SSH_PORT", "22")))
    ap.add_argument("--username", default=os.environ.get("OCH_SSH_USER", "administrator"))
    ap.add_argument("--password", default=os.environ.get("OCH_SSH_PASSWORD", ""))
    ap.add_argument("--sudo-password", default=os.environ.get("OCH_SUDO_PASSWORD", ""))
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--out", default=str(Path("server_migrations") / _now_tag()))
    ap.add_argument("--apply", action="store_true", help="Actually run migrate (otherwise inspection only).")
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
        return 3

    try:
        results.append(run_cmd(c, "hostname && date -Is && uptime", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' 2>&1 || true", timeout=args.timeout))

        # Check that the referenced users migration exists in the live code volume.
        results.append(
            run_sudo_sh(
                c,
                args.sudo_password,
                "docker exec hub_prod_django sh -lc 'ls -la /app/users/migrations | head -n 200' 2>&1 || true",
                timeout=max(args.timeout, 60),
            )
        )
        results.append(
            run_sudo_sh(
                c,
                args.sudo_password,
                "docker exec hub_prod_django sh -lc 'test -f /app/users/migrations/0004_add_metadata_field.py && echo OK:users0004 || echo MISSING:users0004' 2>&1 || true",
                timeout=args.timeout,
            )
        )

        # Introspect DB for presence of django_session (direct SQL through Django).
        results.append(
            run_sudo_sh(
                c,
                args.sudo_password,
                "docker exec hub_prod_django python - <<'PY'\nfrom django.db import connection\nimport os\nos.environ.setdefault('DJANGO_SETTINGS_MODULE','core.settings.production')\ntry:\n    with connection.cursor() as cur:\n        cur.execute(\"select to_regclass('public.django_session')\")\n        print('django_session_regclass=', cur.fetchone()[0])\nexcept Exception as e:\n    print('db_check_error=', type(e).__name__, e)\nPY 2>&1 || true",
                timeout=max(args.timeout, 90),
            )
        )

        # Migration graph inspection
        results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_django python manage.py showmigrations users 2>&1 || true", timeout=max(args.timeout, 90)))
        results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_django python manage.py showmigrations sessions 2>&1 || true", timeout=max(args.timeout, 90)))
        results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_django python manage.py migrate --plan 2>&1 | tail -n 200 || true", timeout=max(args.timeout, 120)))

        if args.apply:
            # Apply migrations (noinput). If graph is broken this will show immediately.
            results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_django python manage.py migrate --noinput 2>&1 || true", timeout=max(args.timeout, 180)))
            # Re-check django_session table
            results.append(
                run_sudo_sh(
                    c,
                    args.sudo_password,
                    "docker exec hub_prod_django python - <<'PY'\nfrom django.db import connection\nwith connection.cursor() as cur:\n    cur.execute(\"select to_regclass('public.django_session')\")\n    print('django_session_regclass=', cur.fetchone()[0])\nPY 2>&1 || true",
                    timeout=max(args.timeout, 90),
                )
            )

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

