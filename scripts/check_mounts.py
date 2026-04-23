import paramiko

host = "69.30.235.220"
user = "administrator"
password = "Ongoza@#1"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=60)

stdin, stdout, stderr = client.exec_command(f"printf '{password}\\n' | sudo -S -p '' docker inspect hub_prod_nginx --format='{{{{json .Mounts}}}}'")
print(stdout.read().decode('utf-8'))
client.close()
