"""One-shot VPS: reset /var/www/och to origin/main, docker pull + up. Password: env OCH_SSH_PASSWORD only."""
import json
import os
import sys

import paramiko


def main() -> None:
    pw = os.environ.get("OCH_SSH_PASSWORD", "").strip()
    if not pw:
        sys.exit("Set OCH_SSH_PASSWORD")

    inner = """set -euo pipefail
cd /var/www/och
git fetch origin
git reset --hard origin/main
docker compose pull nextjs django fastapi || true
docker compose up -d
docker compose ps
git log -1 --oneline
echo SNAP_DEPLOY_DONE
"""

    remote = (
        "export SUDO_PASSWORD="
        + json.dumps(pw)
        + "\n"
        + "printf '%s\\n' \"$SUDO_PASSWORD\" | sudo -S -p '' bash -lc "
        + json.dumps(inner)
        + "\n"
    )

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect("69.30.235.220", username="administrator", password=pw, timeout=90, banner_timeout=90)
    stdin, stdout, stderr = c.exec_command("bash -s", timeout=3600, get_pty=True)
    stdin.write(remote.encode())
    stdin.channel.shutdown_write()
    sys.stdout.write(stdout.read().decode("utf-8", errors="replace"))
    sys.stderr.write(stderr.read().decode("utf-8", errors="replace"))
    code = stdout.channel.recv_exit_status()
    c.close()
    sys.exit(code)


if __name__ == "__main__":
    main()
