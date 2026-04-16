import paramiko
import time

host = "69.30.235.220"
ssh_user = "administrator"
password = "Ongoza@#1"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=ssh_user, password=password)

print("=== PULLING LATEST CODE ===")
transport = client.get_transport()

ch1 = transport.open_session()
ch1.get_pty()
# We run as sudo just in case permissions require it
ch1.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' bash -c 'cd /var/www/och && git pull origin main'")
for _ in range(20):
    time.sleep(0.5)
    while ch1.recv_ready():
        print(ch1.recv(4096).decode(errors='replace'), end="", flush=True)
    if ch1.exit_status_ready():
        break
while ch1.recv_ready():
    print(ch1.recv(4096).decode(errors='replace'), end="", flush=True)
print()

print("\n=== REBUILDING NEXTJS CONTAINER ===")
ch2 = transport.open_session()
ch2.get_pty()
ch2.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' bash -c 'cd /var/www/och && docker-compose build nextjs && docker-compose up -d nextjs'")
for _ in range(300):  # Wait up to 150 seconds for build
    time.sleep(0.5)
    while ch2.recv_ready():
        print(ch2.recv(4096).decode(errors='replace'), end="", flush=True)
    if ch2.exit_status_ready():
        break
while ch2.recv_ready():
    print(ch2.recv(4096).decode(errors='replace'), end="", flush=True)
print("\n=== DONE ===")

client.close()
