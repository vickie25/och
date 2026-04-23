import os, sys, paramiko
pw = os.environ.get("OCH_SSH_PASSWORD", "").strip()
if not pw:
    sys.exit("missing OCH_SSH_PASSWORD")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("69.30.235.220", username="administrator", password=pw, timeout=45)
cmd = """echo '=== log (last 30 lines) ==='; test -f /tmp/och_docker_pull.log && tail -30 /tmp/och_docker_pull.log || echo 'NO_LOG_FILE'; echo '=== DONE_UP? ==='; grep -n DONE_UP /tmp/och_docker_pull.log 2>/dev/null || echo 'NO_DONE_YET'; echo '=== docker compose ps (nextjs line) ==='; cd /var/www/och 2>/dev/null && docker compose ps 2>/dev/null | head -20 || sudo docker compose ps 2>/dev/null | head -20 || echo 'compose_ps_failed'"""
_, o, e = c.exec_command(cmd, timeout=90)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err:
    print(err, file=sys.stderr)
c.close()
