"""SSH: start docker compose pull+up as root in background; log /tmp/och_docker_pull.log. Env OCH_SSH_PASSWORD."""
import json
import os
import sys

import paramiko

PW = os.environ.get("OCH_SSH_PASSWORD", "").strip()
if not PW:
    sys.exit("missing OCH_SSH_PASSWORD")

# Whole block runs as root (sudo); pull/up continues after SSH returns.
inner = """set -e
cd /var/www/och
: > /tmp/och_docker_pull.log
nohup bash -c 'cd /var/www/och && docker compose pull nextjs django fastapi >> /tmp/och_docker_pull.log 2>&1 && docker compose up -d >> /tmp/och_docker_pull.log 2>&1 && echo DONE_UP >> /tmp/och_docker_pull.log' &
sleep 3
tail -40 /tmp/och_docker_pull.log || true
echo "--- tail above; full log: /tmp/och_docker_pull.log ---"
"""

remote = (
    "export SUDO_PASSWORD="
    + json.dumps(PW)
    + "\n"
    + "printf '%s\\n' \"$SUDO_PASSWORD\" | sudo -S -p '' bash -lc "
    + json.dumps(inner)
    + "\n"
)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("69.30.235.220", username="administrator", password=PW, timeout=60)
stdin, stdout, stderr = c.exec_command("bash -s", timeout=120, get_pty=True)
stdin.write(remote.encode())
stdin.channel.shutdown_write()
sys.stdout.write(stdout.read().decode(errors="replace"))
sys.stderr.write(stderr.read().decode(errors="replace"))
code = stdout.channel.recv_exit_status()
c.close()
sys.exit(code)
