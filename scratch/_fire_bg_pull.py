import json, os, sys, paramiko
pw = os.environ["OCH_SSH_PASSWORD"].strip()
inner = """set -e
cd /var/www/och
: > /tmp/och_docker_pull.log
nohup bash -c 'cd /var/www/och && docker compose pull nextjs django fastapi >> /tmp/och_docker_pull.log 2>&1 && docker compose up -d >> /tmp/och_docker_pull.log 2>&1 && echo DONE_UP >> /tmp/och_docker_pull.log' &
disown || true
sleep 2
ls -la /tmp/och_docker_pull.log
head -5 /tmp/och_docker_pull.log || true
echo FIRED_OK
"""
r = "export SUDO_PASSWORD=" + json.dumps(pw) + "\n" + "printf '%s\\n' \"$SUDO_PASSWORD\" | sudo -S -p '' bash -lc " + json.dumps(inner) + "\n"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("69.30.235.220", username="administrator", password=pw, timeout=45)
i, o, e = c.exec_command("bash -s", timeout=90, get_pty=True)
i.write(r.encode())
i.channel.shutdown_write()
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace"), file=sys.stderr)
sys.exit(o.channel.recv_exit_status())
