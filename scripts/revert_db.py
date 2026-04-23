import paramiko
import re

host = "69.30.235.220"
user = "administrator"
password = "Ongoza@#1"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=60)

def run_sudo(cmd):
    stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}")
    return stdout.read().decode('utf-8', 'ignore').strip()

print("Reverting Django DB to local postgres-relational to restore platform uptime...")

env_path = "/var/www/och/backend/django_app/.env"
content = run_sudo(f"cat {env_path}")

new_content = re.sub(r'POSTGRES_USER=.*', 'POSTGRES_USER=postgres', content)
new_content = re.sub(r'POSTGRES_PASSWORD=.*', 'POSTGRES_PASSWORD=postgres', new_content)
new_content = re.sub(r'POSTGRES_HOST=.*', 'POSTGRES_HOST=postgres-relational', new_content)

escaped_content = new_content.replace("\\", "\\\\").replace("$", "\\$").replace("`", "\\`")
write_cmd = f'cat << \'EOF\' > /tmp/env_patch.conf\n{new_content}\nEOF'
client.exec_command(write_cmd)

run_sudo(f"cp /tmp/env_patch.conf {env_path}")
run_sudo("cd /var/www/och && docker-compose restart django")

print("Done. The site will now stay online, but the data is the ransomed local data.")
client.close()
