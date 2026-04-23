import paramiko

def volume_size_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Total Volume Size Audit...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Listing all volumes and their sizes
        print("\n--- DOCKER VOLUMES (SIZES) ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' du -sh /var/lib/docker/volumes/* | sort -h"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))
        
        # 2. Specifically look for postgres data folders
        print("\n--- POSTGRES DATA FOLDERS ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' find /var/lib/docker/volumes/ -name 'PG_VERSION' -exec dirname {{}} \\; | xargs sudo du -sh"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    volume_size_audit()
