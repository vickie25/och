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
    ap = argparse.ArgumentParser(description="Verify Redis operational status on VPS.")
    ap.add_argument("--host", default=os.environ.get("OCH_SSH_HOST", "69.30.235.220"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("OCH_SSH_PORT", "22")))
    ap.add_argument("--username", default=os.environ.get("OCH_SSH_USER", "administrator"))
    ap.add_argument("--password", default=os.environ.get("OCH_SSH_PASSWORD", ""))
    ap.add_argument("--sudo-password", default=os.environ.get("OCH_SUDO_PASSWORD", ""))
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--out", default=str(Path("server_redis") / _now_tag()))
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
        # 1) Is Redis deployed as a container?
        results.append(run_sudo_sh(c, args.sudo_password, "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' | (grep -i redis || true)", timeout=args.timeout))

        # 2) Is Redis deployed as a system service?
        results.append(run_sudo_sh(c, args.sudo_password, "systemctl status redis redis-server --no-pager 2>&1 || true", timeout=args.timeout))

        # 3) Is anything listening on 6379 (host level)?
        results.append(run_sudo_sh(c, args.sudo_password, "ss -lntp 2>/dev/null | (grep ':6379' || true)", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "netstat -lntp 2>/dev/null | (grep ':6379' || true)", timeout=args.timeout))

        # 4) Connectivity check to localhost:6379
        results.append(run_sudo_sh(c, args.sudo_password, "timeout 2 bash -lc 'echo -e \"PING\\r\\n\" | nc -w 1 127.0.0.1 6379' 2>&1 || true", timeout=args.timeout))

        # 5) Docker network sanity: which compose network exists?
        results.append(run_sudo_sh(c, args.sudo_password, "docker network ls 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "docker network inspect och_prod_network 2>&1 || true", timeout=max(args.timeout, 60)))

        # 6) From Django container: does DNS resolve redis? does TCP connect?
        results.append(
            run_sudo_sh(
                c,
                args.sudo_password,
                "docker exec hub_prod_django python -c \"import socket; hosts=['redis','hub_prod_redis','localhost'];\nfor h in hosts:\n  \n  try: print(h, socket.gethostbyname(h))\n  except Exception as e: print(h,'RESOLVE_FAIL',e)\" 2>&1 || true",
                timeout=max(args.timeout, 60),
            )
        )
        results.append(
            run_sudo_sh(
                c,
                args.sudo_password,
                "docker exec hub_prod_django python -c \"import socket; \n\ndef probe(h,p):\n  s=socket.socket(); s.settimeout(2)\n  try: s.connect((h,p)); print(h,p,'CONNECT_OK')\n  except Exception as e: print(h,p,'CONNECT_FAIL',type(e).__name__,e)\n  finally:\n    \n    try: s.close()\n    except: pass\n\nfor h in ['redis','hub_prod_redis','127.0.0.1']:\n  probe(h,6379)\" 2>&1 || true",
                timeout=max(args.timeout, 60),
            )
        )

        # 6b) Are the containers on same network? (needs docker inspect)
        results.append(run_sudo_sh(c, args.sudo_password, "docker inspect -f '{{json .NetworkSettings.Networks}}' hub_prod_django 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "docker inspect -f '{{json .NetworkSettings.Networks}}' hub_prod_redis 2>&1 || true", timeout=args.timeout))

        # 7) If redis-cli exists anywhere, run a ping (best effort)
        results.append(run_sudo_sh(c, args.sudo_password, "command -v redis-cli >/dev/null 2>&1 && redis-cli -h 127.0.0.1 -p 6379 ping 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "docker exec hub_prod_django sh -lc 'command -v redis-cli >/dev/null 2>&1 && redis-cli -h redis -p 6379 ping' 2>&1 || true", timeout=args.timeout))

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

