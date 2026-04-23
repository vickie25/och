import argparse
import datetime as dt
import json
import os
import re
import socket
from dataclasses import dataclass
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


@dataclass(frozen=True)
class Container:
    name: str
    image: str


def parse_containers(table: str) -> list[Container]:
    # Expects lines like: "<name>\t<image>"
    out: list[Container] = []
    for raw in (table or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        name, image = parts[0].strip(), parts[1].strip()
        if name and image:
            out.append(Container(name=name, image=image))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Discover deployed stack + DB containers remotely.")
    ap.add_argument("--host", default=os.environ.get("OCH_SSH_HOST", "69.30.235.220"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("OCH_SSH_PORT", "22")))
    ap.add_argument("--username", default=os.environ.get("OCH_SSH_USER", "administrator"))
    ap.add_argument("--password", default=os.environ.get("OCH_SSH_PASSWORD", ""))
    ap.add_argument("--sudo-password", default=os.environ.get("OCH_SUDO_PASSWORD", ""))
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--remote-root", default="/var/www/och")
    ap.add_argument("--out", default=str(Path("server_discovery") / _now_tag()))
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
        results.append(run_cmd(c, "whoami && hostname && uptime", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "docker --version || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "docker-compose version || true", timeout=args.timeout))

        # Compose file presence + services
        results.append(run_sudo_sh(c, args.sudo_password, f"ls -la {args.remote_root} || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, f"ls -la {args.remote_root}/docker-compose.yml || true", timeout=args.timeout))
        results.append(
            run_sudo_sh(
                c,
                args.sudo_password,
                f"cd {args.remote_root} && (sed -n '1,220p' docker-compose.yml 2>/dev/null || true)",
                timeout=max(args.timeout, 60),
            )
        )
        results.append(run_sudo_sh(c, args.sudo_password, f"cd {args.remote_root} && docker-compose config --services 2>&1 || true", timeout=max(args.timeout, 60)))
        results.append(run_sudo_sh(c, args.sudo_password, f"cd {args.remote_root} && docker-compose ps -a 2>&1 || true", timeout=max(args.timeout, 60)))

        # Containers and networks
        r_list = run_sudo_sh(
            c,
            args.sudo_password,
            "docker ps -a --format '{{.Names}}\t{{.Image}}' || true",
            timeout=args.timeout,
        )
        results.append(r_list)

        results.append(run_sudo_sh(c, args.sudo_password, "docker network ls 2>&1 || true", timeout=args.timeout))
        results.append(run_sudo_sh(c, args.sudo_password, "docker network inspect ongoza-network 2>&1 || true", timeout=max(args.timeout, 60)))

        containers = parse_containers(r_list.get("stdout", ""))
        pg_candidates = [ct for ct in containers if "postgres" in ct.image.lower()]

        # If we can find postgres images, probe readiness + db list.
        for ct in pg_candidates[:6]:
            results.append(run_sudo_sh(c, args.sudo_password, f"docker exec {ct.name} pg_isready -U postgres 2>&1 || true", timeout=args.timeout))
            results.append(run_sudo_sh(c, args.sudo_password, f"docker exec {ct.name} psql -U postgres -c \"\\l\" 2>&1 || true", timeout=max(args.timeout, 60)))

        # If we can find the compose-defined postgres containers by label, list them too.
        results.append(
            run_sudo_sh(
                c,
                args.sudo_password,
                "docker ps -a --filter 'label=com.docker.compose.project' --format 'table {{.Names}}\t{{.Label \"com.docker.compose.service\"}}\t{{.Status}}' 2>&1 || true",
                timeout=max(args.timeout, 60),
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

