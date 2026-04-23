import paramiko

def global_backup_hunt():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Searching for manual SQL backups on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Searching for any substantial SQL or dump files
        # We look for files larger than 1MB to avoid small scripts
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' find / -type f \( -name '*.sql' -o -name '*.dump' -o -name '*.tar' -o -name '*.pgsql' \) -size +1M -not -path '*/proc/*' -not -path '*/sys/*' 2>/dev/null"
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- POTENTIAL BACKUPS FOUND ---")
        found = stdout.read().decode('utf-8', errors='ignore').splitlines()
        for path in found:
            print(f"Backup: {path.strip()}")
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    global_backup_hunt()
