import argparse
import datetime as dt
import json
import os
import re
import socket
import sys
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

    # Also write a human-readable rollup.
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Pull remote logs via Paramiko (read-only).")
    ap.add_argument("--host", default=os.environ.get("OCH_SSH_HOST", "69.30.235.220"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("OCH_SSH_PORT", "22")))
    ap.add_argument("--username", default=os.environ.get("OCH_SSH_USER", "administrator"))
    ap.add_argument("--password", default=os.environ.get("OCH_SSH_PASSWORD", ""))
    ap.add_argument("--sudo-password", default=os.environ.get("OCH_SUDO_PASSWORD", ""))
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--remote-root", default="/var/www/och")
    ap.add_argument("--tail", type=int, default=400)
    ap.add_argument("--out", default=str(Path("server_logs") / _now_tag()))
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
        # Basic identity / uptime / disk / memory
        results.append(run_cmd(c, "whoami && hostname && uptime", timeout=args.timeout))
        results.append(run_cmd(c, "date -Is && uname -a", timeout=args.timeout))
        results.append(run_cmd(c, "df -h", timeout=args.timeout))
        results.append(run_cmd(c, "free -m || vmstat -s", timeout=args.timeout))

        # Recent auth/suspicious activity (requires sudo)
        results.append(run_sudo_sh(c, args.sudo_password, f"last -n 80 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, f"who -a || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, f"journalctl -u ssh --no-pager -n {args.tail} || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, f"journalctl --since '2 hours ago' --no-pager -n {args.tail} || true", timeout=args.timeout))

        # Docker + compose status/logs
        results.append(run_sudo_sh(c, args.sudo_password, "docker ps -a || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "docker stats --no-stream || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, f"cd {args.remote_root} && (docker compose ps || docker-compose ps) || true", timeout=args.timeout))
        results.append(
            run_sudo_sh(
                c,
                args.sudo_password,
                f"cd {args.remote_root} && ((docker compose logs --no-color --tail {args.tail}) || (docker-compose logs --tail {args.tail})) || true",
                timeout=max(args.timeout, 60),
            )
        )

        # Per-container logs (common names from compose)
        for name in ["hub_prod_nginx", "hub_prod_django", "hub_prod_fastapi", "hub_prod_postgres", "hub_prod_vector_db", "hub_prod_redis", "hub_prod_nextjs"]:
            results.append(
                run_sudo_sh(
                    c,
                    args.sudo_password,
                    f"docker logs --tail {args.tail} {name} 2>&1 || true",
                    timeout=max(args.timeout, 60),
                )
            )

        # Nginx + app logs on filesystem (best effort)
        results.append(run_sudo_sh(c, args.sudo_password, f"ls -la /var/log/nginx || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, f"tail -n {args.tail} /var/log/nginx/error.log 2>/dev/null || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, f"tail -n {args.tail} /var/log/nginx/access.log 2>/dev/null || true", timeout=args.timeout))

        # Env presence checks (do not print env contents)
        results.append(
            run_sudo_sh(
                c,
                args.sudo_password,
                f"cd {args.remote_root} && ls -la backend/django_app/.env 2>/dev/null || echo 'missing: backend/django_app/.env'",
                timeout=args.timeout,
            )
        )
        results.append(
            run_sudo_sh(
                c,
                args.sudo_password,
                f"cd {args.remote_root} && ls -la .env 2>/dev/null || echo 'missing: .env (compose root env file)'",
                timeout=args.timeout,
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

