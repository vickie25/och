"""SSH: docker compose ps + logs. Env: OCH_SSH_PASSWORD."""
import base64
import json
import os
import sys

import paramiko

PW = os.environ.get("OCH_SSH_PASSWORD", "").strip()
if not PW:
    sys.exit("Set OCH_SSH_PASSWORD")

cmd = """set -e
cd /var/www/och
echo '========== docker compose ps =========='
docker compose ps 2>&1
echo ''
echo '========== nextjs (last 35 lines) =========='
docker compose logs --tail 35 nextjs 2>&1
echo ''
echo '========== django (last 35 lines) =========='
docker compose logs --tail 35 django 2>&1
echo ''
echo '========== fastapi (last 35 lines) =========='
docker compose logs --tail 35 fastapi 2>&1
echo ''
echo '========== nginx (last 20 lines) =========='
docker compose logs --tail 20 nginx 2>&1 || true
"""

b64 = base64.b64encode(cmd.encode("utf-8")).decode("ascii")
# decode and run as root so docker works without group issues
remote = (
    "printf '%s\\n' "
    + json.dumps(PW)
    + " | sudo -S -p '' bash -c "
    + json.dumps(f"echo {b64} | base64 -d | bash")
    + "\n"
)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("69.30.235.220", username="administrator", password=PW, timeout=45)
stdin, stdout, stderr = c.exec_command("bash -s", timeout=180)
stdin.write(remote.encode())
stdin.channel.shutdown_write()
sys.stdout.write(stdout.read().decode(errors="replace"))
e = stderr.read().decode(errors="replace")
if e:
    sys.stderr.write(e)
c.close()
