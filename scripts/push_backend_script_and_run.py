import argparse
import os
import socket
import sys
from pathlib import Path

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
    ap = argparse.ArgumentParser(description="Push a backend script to VPS and run it inside Django container.")
    ap.add_argument("--host", default=os.environ.get("OCH_SSH_HOST", "69.30.235.220"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("OCH_SSH_PORT", "22")))
    ap.add_argument("--username", default=os.environ.get("OCH_SSH_USER", "administrator"))
    ap.add_argument("--password", default=os.environ.get("OCH_SSH_PASSWORD", ""))
    ap.add_argument("--sudo-password", default=os.environ.get("OCH_SUDO_PASSWORD", ""))
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--remote-root", default="/var/www/och")
    ap.add_argument("--local-path", required=True)
    ap.add_argument("--remote-relpath", required=True)
    ap.add_argument("--docker-run", default="")
    args = ap.parse_args()

    if not args.password:
        print("Missing SSH password.")
        return 2
    if not args.sudo_password:
        args.sudo_password = args.password

    local_path = Path(args.local_path).resolve()
    if not local_path.exists():
        print(f"Local file missing: {local_path}")
        return 4

    remote_path = f"{args.remote_root}/{args.remote_relpath}".replace("\\", "/")
    remote_dir = str(Path(remote_path).parent).replace("\\", "/")

    try:
        c = ssh_connect(args.host, args.username, args.password, args.port, timeout=args.timeout)
    except (paramiko.AuthenticationException, paramiko.SSHException, socket.timeout, OSError) as e:
        print(f"SSH connect failed: {e}")
        return 3

    try:
        # Ensure destination directory exists
        run_sudo_sh(c, args.sudo_password, f"mkdir -p '{remote_dir}'", timeout=max(args.timeout, 60))

        # Upload to /tmp and install with sudo
        sftp = c.open_sftp()
        tmp_remote = f"/tmp/{local_path.name}"
        sftp.put(str(local_path), tmp_remote)
        sftp.close()

        _, out, err = run_sudo_sh(
            c,
            args.sudo_password,
            f"install -m 0644 '{tmp_remote}' '{remote_path}' && ls -la '{remote_path}'",
            timeout=max(args.timeout, 60),
        )
        if out.strip():
            sys.stdout.buffer.write(out.strip().encode("utf-8", errors="replace"))
            sys.stdout.buffer.write(b"\n")
        if err.strip():
            sys.stderr.buffer.write(err.strip().encode("utf-8", errors="replace"))
            sys.stderr.buffer.write(b"\n")

        if args.docker_run:
            _, out2, err2 = run_sudo_sh(c, args.sudo_password, args.docker_run, timeout=max(args.timeout, 180))
            if out2.strip():
                sys.stdout.buffer.write(out2.strip().encode("utf-8", errors="replace"))
                sys.stdout.buffer.write(b"\n")
            if err2.strip():
                sys.stderr.buffer.write(err2.strip().encode("utf-8", errors="replace"))
                sys.stderr.buffer.write(b"\n")

    finally:
        try:
            c.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

