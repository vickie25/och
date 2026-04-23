import paramiko

host = "69.30.235.220"
user = "administrator"
password = "Ongoza@#1"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=60)

print("Finding URLs in Django...")
stdin, stdout, stderr = client.exec_command(f"printf '{password}\\n' | sudo -S -p '' docker exec hub_prod_django find /app -name urls.py -path '*/core/*' -exec cat {{}} +")
print(stdout.read().decode('utf-8', 'ignore'))

client.close()
