import paramiko

def data_folder_hunt():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Hunting for data folders on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Check standard project directory for data folders
        print("\n--- DIRECTORY SCAN (/var/www/och) ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' find /var/www/och -maxdepth 3 -name '*data*' -type d"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    data_folder_hunt()
