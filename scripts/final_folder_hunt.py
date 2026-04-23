import paramiko

def final_folder_hunt():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Final Folder Hunt for Database ID 16384...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Searching for '16384', which identifies a populated postgres data directory
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' find / -name '16384' -type d -not -path '*/proc/*' -not -path '*/sys/*' 2>/dev/null"
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- POPULATED FOLDERS FOUND ---")
        found = stdout.read().decode('utf-8', errors='ignore').splitlines()
        for path in found:
            print(f"Location: {path.strip()}")
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    final_folder_hunt()
