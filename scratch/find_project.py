import paramiko
import time

host = "69.30.235.220"
ssh_user = "administrator"
password = "Ongoza@#1"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=ssh_user, password=password)

transport = client.get_transport()

# Find where the project lives
ch1 = transport.open_session()
ch1.get_pty()
ch1.exec_command("find /home /opt /srv /var/www -name 'docker-compose.yml' 2>/dev/null | head -10; docker ps --format '{{.Names}} {{.Image}}' | head -20")
output = ""
for _ in range(20):
    time.sleep(0.5)
    while ch1.recv_ready():
        output += ch1.recv(4096).decode(errors='replace')
    if ch1.exit_status_ready():
        break
while ch1.recv_ready():
    output += ch1.recv(4096).decode(errors='replace')
print(output)

client.close()
