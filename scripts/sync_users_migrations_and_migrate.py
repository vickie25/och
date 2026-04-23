import argparse
import datetime as dt
import os
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
    ap = argparse.ArgumentParser(description="Sync users migrations to VPS and run migrate.")
    ap.add_argument("--host", default=os.environ.get("OCH_SSH_HOST", "69.30.235.220"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("OCH_SSH_PORT", "22")))
    ap.add_argument("--username", default=os.environ.get("OCH_SSH_USER", "administrator"))
    ap.add_argument("--password", default=os.environ.get("OCH_SSH_PASSWORD", ""))
    ap.add_argument("--sudo-password", default=os.environ.get("OCH_SUDO_PASSWORD", ""))
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--remote-root", default="/var/www/och")
    ap.add_argument("--local-migrations-dir", default=str(Path("backend/django_app/users/migrations")))
    args = ap.parse_args()

    if not args.password:
        print("Missing SSH password.")
        return 2
    if not args.sudo_password:
        args.sudo_password = args.password

    local_dir = Path(args.local_migrations_dir).resolve()
    if not local_dir.exists():
        print(f"Local migrations dir not found: {local_dir}")
        return 4

    local_files = sorted([p for p in local_dir.glob("*.py") if p.is_file()])
    if not local_files:
        print(f"No migration .py files found in {local_dir}")
        return 5

    remote_dir = f"{args.remote_root}/backend/django_app/users/migrations"

    try:
        c = ssh_connect(args.host, args.username, args.password, args.port, timeout=args.timeout)
    except (paramiko.AuthenticationException, paramiko.SSHException, socket.timeout, OSError) as e:
        print(f"SSH connect failed: {e}")
        return 3

    try:
        # Ensure remote dir exists and is writable via sudo.
        run_sudo_sh(c, args.sudo_password, f"mkdir -p '{remote_dir}' && ls -la '{remote_dir}' | head -n 40", timeout=max(args.timeout, 60))

        # Upload each migration to /tmp then install into place (preserve perms).
        sftp = c.open_sftp()
        tmp_base = f"/tmp/users_migrations_{_now_tag()}"
        run_sudo_sh(c, args.sudo_password, f"mkdir -p '{tmp_base}' && chown {args.username}:{args.username} '{tmp_base}'", timeout=max(args.timeout, 60))

        uploaded = 0
        for p in local_files:
            tmp_remote = f"{tmp_base}/{p.name}"
            sftp.put(str(p), tmp_remote)
            uploaded += 1
        sftp.close()

        # Install into target directory
        code, out, err = run_sudo_sh(
            c,
            args.sudo_password,
            f"install -m 0644 {tmp_base}/*.py '{remote_dir}/' && ls -la '{remote_dir}' | egrep '000[0-9]_' || true",
            timeout=max(args.timeout, 90),
        )
        print(out.strip())
        if err.strip():
            print(err.strip())
        print(f"Uploaded {uploaded} migration files.")

        # Confirm container sees them (volume mount)
        _, out2, err2 = run_sudo_sh(
            c,
            args.sudo_password,
            "docker exec hub_prod_django sh -lc 'ls -la /app/users/migrations | egrep \"000[0-9]_\" || true'",
            timeout=max(args.timeout, 60),
        )
        print(out2.strip())
        if err2.strip():
            print(err2.strip())

        # NOTE: At this stage, we only synced users migrations. Other apps may still
        # have merge conflicts and block `migrate`. We'll run migrate anyway and
        # surface actionable errors.
        _, out3, err3 = run_sudo_sh(
            c,
            args.sudo_password,
            "docker exec hub_prod_django python manage.py migrate --noinput 2>&1 || true",
            timeout=max(args.timeout, 300),
        )
        print(out3.strip())
        if err3.strip():
            print(err3.strip())

        # Verify django_session existence
        _, out4, err4 = run_sudo_sh(
            c,
            args.sudo_password,
            "docker exec hub_prod_django python - <<'PY'\nfrom django.db import connection\nwith connection.cursor() as cur:\n    cur.execute(\"select to_regclass('public.django_session')\")\n    print(cur.fetchone()[0])\nPY",
            timeout=max(args.timeout, 90),
        )
        print(f"django_session_regclass={out4.strip()}")
        if err4.strip():
            print(err4.strip())

        # Restart backend
        run_sudo_sh(c, args.sudo_password, f"cd {args.remote_root} && docker-compose restart backend", timeout=max(args.timeout, 90))

    finally:
        try:
            c.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

