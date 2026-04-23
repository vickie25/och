import argparse
import datetime as dt
import os
import re
import socket

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


def run_cmd(c: paramiko.SSHClient, cmd: str, timeout: int) -> tuple[int, str, str]:
    stdin, stdout, stderr = c.exec_command(cmd, get_pty=False, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="ignore")
    err = stderr.read().decode("utf-8", errors="ignore")
    exit_status = stdout.channel.recv_exit_status()
    return exit_status, out, err


def run_sudo_sh(c: paramiko.SSHClient, sudo_password: str, sh_cmd: str, timeout: int) -> tuple[int, str, str]:
    safe = sh_cmd.replace('"', '\\"')
    cmd = f'printf "{sudo_password}\\n" | sudo -S -p "" sh -c "{safe}"'
    return run_cmd(c, cmd, timeout=timeout)


def main() -> int:
    ap = argparse.ArgumentParser(description="Read remote env URL-ish vars for debugging (safe).")
    ap.add_argument("--host", default=os.environ.get("OCH_SSH_HOST", "69.30.235.220"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("OCH_SSH_PORT", "22")))
    ap.add_argument("--username", default=os.environ.get("OCH_SSH_USER", "administrator"))
    ap.add_argument("--password", default=os.environ.get("OCH_SSH_PASSWORD", ""))
    ap.add_argument("--sudo-password", default=os.environ.get("OCH_SUDO_PASSWORD", ""))
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--remote-root", default="/var/www/och")
    args = ap.parse_args()

    if not args.password:
        print("Missing SSH password.")
        return 2
    if not args.sudo_password:
        args.sudo_password = args.password

    try:
        c = ssh_connect(args.host, args.username, args.password, args.port, timeout=args.timeout)
    except (paramiko.AuthenticationException, paramiko.SSHException, socket.timeout, OSError) as e:
        print(f"SSH connect failed: {e}")
        return 3

    try:
        # These are not secrets; we need actual values to fix Host/DNS issues.
        patterns = r"(DJANGO_.*URL|NEXT_PUBLIC_.*URL|FASTAPI_.*URL|GOOGLE_.*REDIRECT|ALLOWED_HOSTS|CSRF_TRUSTED_ORIGINS|CORS_ALLOWED_ORIGINS)"
        cmd = (
            f"cd {args.remote_root} && "
            + r"echo '--- root .env ---' && "
            + rf"(test -f .env && egrep -n '{patterns}' .env || true) && "
            + r"echo '--- backend .env ---' && "
            + rf"(test -f backend/django_app/.env && egrep -n '{patterns}' backend/django_app/.env || true)"
        )
        _, out, err = run_sudo_sh(c, args.sudo_password, cmd, timeout=max(args.timeout, 60))
        print(out)
        if err.strip():
            print(err)
    finally:
        try:
            c.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

