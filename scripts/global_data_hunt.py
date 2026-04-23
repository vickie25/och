import paramiko

def global_data_hunt():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Initiating Global Data Hunt for PG_VERSION...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Searching for PG_VERSION, which identifies a postgres data directory
        # Excluding /proc, /sys, /dev to avoid virtual filesystems
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' find / -name PG_VERSION -not -path '*/proc/*' -not -path '*/sys/*' -not -path '*/dev/*' 2>/dev/null"
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- DATA HEARTS FOUND ---")
        found = stdout.read().decode('utf-8', errors='ignore').splitlines()
        for path in found:
            print(f"Location: {path.strip()}")
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    global_data_hunt()
