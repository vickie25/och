import paramiko

def database_id_sniff():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Sniffing Database Internal IDs on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # We look for the base directories and their sizes
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' du -m --max-depth=1 /var/lib/docker/volumes/och_postgres_data/_data/base 2>/dev/null"
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- DATABASE INTERNAL FOLDERS (MB) ---")
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    database_id_sniff()
