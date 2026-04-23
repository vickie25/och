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
    (re.compile(r"ssh-(rsa|ed25519)\s+[A-Za-z0-9+/=]+"), "ssh-<redacted-key>"),
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
    ap = argparse.ArgumentParser(description="Recent security audit (auth + miner indicators).")
    ap.add_argument("--host", default=os.environ.get("OCH_SSH_HOST", "69.30.235.220"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("OCH_SSH_PORT", "22")))
    ap.add_argument("--username", default=os.environ.get("OCH_SSH_USER", "administrator"))
    ap.add_argument("--password", default=os.environ.get("OCH_SSH_PASSWORD", ""))
    ap.add_argument("--sudo-password", default=os.environ.get("OCH_SUDO_PASSWORD", ""))
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--since", default="6 hours ago", help="journalctl --since value (e.g. '1 hour ago')")
    ap.add_argument("--out", default=str(Path("server_security") / _now_tag()))
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
        results.append(run_cmd(c, "whoami && hostname && date -Is && uptime", timeout=args.timeout))

        # Auth + sshd logs
        results.append(run_sudo_sh(c, args.sudo_password, f"journalctl -u ssh --since '{args.since}' --no-pager -n 400 2>&1 || true", timeout=max(args.timeout, 60)))
        results.append(run_sudo_sh(c, args.sudo_password, f"journalctl -u sshd --since '{args.since}' --no-pager -n 400 2>&1 || true", timeout=max(args.timeout, 60)))
        results.append(run_sudo_sh(c, args.sudo_password, f"journalctl --since '{args.since}' --no-pager | egrep -i 'sshd\\[|failed password|accepted password|invalid user|pam_unix\\(sshd|sudo\\:' | tail -n 250 2>&1 || true", timeout=max(args.timeout, 60)))
        results.append(run_sudo_sh(c, args.sudo_password, "last -n 50 2>&1 || true", timeout=args.timeout))

        # Common auth log files (Ubuntu/Debian)
        results.append(run_sudo_sh(c, args.sudo_password, "test -f /var/log/auth.log && tail -n 250 /var/log/auth.log || echo 'no /var/log/auth.log' ", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "test -f /var/log/secure && tail -n 250 /var/log/secure || echo 'no /var/log/secure' ", timeout=args.timeout))

        # Miner / malware indicators
        results.append(run_sudo_sh(c, args.sudo_password, "ps aux --sort=-%cpu | head -n 25 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "ps aux --sort=-%mem | head -n 25 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "ss -tunap 2>/dev/null | head -n 80 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "crontab -l 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "ls -la /etc/cron.* 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "systemctl list-units --type=service --state=running --no-pager 2>&1 | head -n 200 || true", timeout=max(args.timeout, 60)))
        results.append(run_sudo_sh(c, args.sudo_password, "systemctl list-timers --all --no-pager 2>&1 || true", timeout=max(args.timeout, 60)))

        # Users and SSH authorized keys (do not print key contents)
        results.append(run_sudo_sh(c, args.sudo_password, "getent passwd | egrep -v '^(root|daemon|bin|sys|sync|games|man|lp|mail|news|uucp|proxy|www-data|backup|list|irc|gnats|nobody|systemd-.*|messagebus|_apt|uuidd|sshd):' 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "ls -la /home/*/.ssh/authorized_keys 2>/dev/null || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "stat /home/*/.ssh/authorized_keys 2>/dev/null || true", timeout=args.timeout))

        # Docker recent restarts (sometimes miners run in containers)
        results.append(run_sudo_sh(c, args.sudo_password, "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}' | head -n 60 2>&1 || true", timeout=args.timeout))

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

