import shlex
import os
import sys
import paramiko
pw = os.environ.get("OCH_SSH_PASSWORD", "").strip()
if not pw:
    sys.exit("Set OCH_SSH_PASSWORD")
q = shlex.quote(pw)
cmd = f"cd /var/www/och && printf '%s\\n' {q} | sudo -S -p '' docker-compose ps"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("69.30.235.220", username="administrator", password=pw, timeout=30)
_, o, e = c.exec_command(cmd, timeout=90)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err:
    print(err, file=sys.stderr)
c.close()
