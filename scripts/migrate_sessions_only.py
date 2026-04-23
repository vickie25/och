import argparse
import os
import socket

import paramiko


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
    ap = argparse.ArgumentParser(description="Apply only Django sessions migrations on VPS.")
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
        # Run migrations for sessions only (should avoid unrelated DuplicateTable issues).
        _, out, err = run_sudo_sh(
            c,
            args.sudo_password,
            "docker exec hub_prod_django python manage.py migrate contenttypes --noinput 2>&1 || true",
            timeout=max(args.timeout, 180),
        )
        print(out.strip())
        if err.strip():
            print(err.strip())

        _, out2, err2 = run_sudo_sh(
            c,
            args.sudo_password,
            "docker exec hub_prod_django python manage.py migrate sessions --noinput 2>&1 || true",
            timeout=max(args.timeout, 180),
        )
        print(out2.strip())
        if err2.strip():
            print(err2.strip())

        # Verify django_session now exists
        _, out3, err3 = run_sudo_sh(
            c,
            args.sudo_password,
            "docker exec hub_prod_django python -c \"from django.db import connection; cur=connection.cursor(); cur.execute(\\\"select to_regclass('public.django_session')\\\"); print(cur.fetchone()[0])\" 2>&1 || true",
            timeout=max(args.timeout, 90),
        )
        print(f"django_session_regclass={out3.strip()}")
        if err3.strip():
            print(err3.strip())

        run_sudo_sh(c, args.sudo_password, f"cd {args.remote_root} && docker-compose restart backend", timeout=max(args.timeout, 90))

        # Test auth initiate endpoint
        _, out4, _ = run_sudo_sh(
            c,
            args.sudo_password,
            "curl -s -o /dev/null -w '%{http_code}\\n' http://127.0.0.1:8000/api/v1/auth/google/initiate?role=student&mode=login || true",
            timeout=max(args.timeout, 30),
        )
        print(f"auth_initiate_http_code={out4.strip()}")

    finally:
        try:
            c.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

