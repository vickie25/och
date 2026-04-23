import json, os, sys, paramiko
pw = os.environ["OCH_SSH_PASSWORD"].strip()
inner = "touch /tmp/och_agent_test.txt && ls -la /tmp/och_agent_test.txt"
r = "export SUDO_PASSWORD=" + json.dumps(pw) + "\n" + "printf '%s\\n' \"$SUDO_PASSWORD\" | sudo -S -p '' bash -lc " + json.dumps(inner) + "\n"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("69.30.235.220", username="administrator", password=pw, timeout=30)
i, o, e = c.exec_command("bash -s", timeout=30, get_pty=True)
i.write(r.encode())
i.channel.shutdown_write()
print(o.read().decode(errors="replace"))
c.close()
