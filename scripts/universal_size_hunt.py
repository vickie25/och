import paramiko

def universal_size_hunt():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Initiating Universal Disk Usage Scan on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # We check the size of ALL volumes in /var/lib/docker/volumes
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' du -m --max-depth=1 /var/lib/docker/volumes/ | sort -rn | head -n 20"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        
        print("\n--- TOP 20 LARGEST VOLUMES (MB) ---")
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    universal_size_hunt()
