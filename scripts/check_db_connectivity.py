import paramiko

host = "69.30.235.220"
user = "administrator"
password = "Ongoza@#1"

try:
    print("Checking database connectivity to 138.197.203.235...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=60)
    
    stdin, stdout, stderr = client.exec_command("nc -vw 3 138.197.203.235 5432 || echo 'DB_UNREACHABLE'")
    print(stdout.read().decode('utf-8', 'ignore'))
    print(stderr.read().decode('utf-8', 'ignore'))

    client.close()
except Exception as e:
    print(f"Error: {e}")
