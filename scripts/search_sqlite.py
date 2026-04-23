import paramiko

host = "69.30.235.220"
user = "administrator"
password = "Ongoza@#1"

try:
    print("Searching for SQLite databases...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=60)
    
    def run_sudo(cmd):
        stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}")
        return stdout.read().decode('utf-8', 'ignore').strip()

    print("\nLocal filesystem SQLite search:")
    # Ignore large system dirs to speed up search
    cmd = "find /var/www/och -type f -name '*.sqlite3' -o -name '*.db' 2>/dev/null"
    print(run_sudo(cmd))

    print("\nContainer internal SQLite search:")
    print(run_sudo("docker exec hub_prod_django find /app -type f -name '*.sqlite3' -o -name '*.db' 2>/dev/null"))

    client.close()
except Exception as e:
    print(f"Error: {e}")
