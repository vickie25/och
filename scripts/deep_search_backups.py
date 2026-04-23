import paramiko

host = "69.30.235.220"
user = "administrator"
password = "Ongoza@#1"

try:
    print("Searching for postgres backups deep in volumes...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=60)
    
    def run_sudo(cmd):
        stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}")
        return stdout.read().decode('utf-8', 'ignore').strip()

    print(run_sudo("find /var/lib/docker/volumes -type f \( -name '*.sql' -o -name '*.dump' -o -name '*.bak' -o -name '*.tar.gz' -o -name 'backup*' \) 2>/dev/null | head -50"))

    client.close()
except Exception as e:
    print(f"Error: {e}")
