import paramiko

host = "69.30.235.220"
user = "administrator"
password = "Ongoza@#1"

try:
    print("Searching for database backups...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=60)
    
    def run_sudo(cmd):
        stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}")
        return stdout.read().decode('utf-8', 'ignore').strip()

    print("\nLooking for .sql or .dump files globally:")
    print(run_sudo("find / -type f \( -name '*.sql' -o -name '*.dump' -o -name '*.bak' \) 2>/dev/null | grep -v '/var/lib/docker' | head -30"))

    client.close()
except Exception as e:
    print(f"Error: {e}")
