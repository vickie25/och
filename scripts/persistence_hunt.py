import paramiko

def persistence_hunt():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Persistence Hunt for Malware Anchor...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Checking root and admin crontabs
        print("\n--- CRONTAB (Root) ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' crontab -l"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))

        print("\n--- CRONTAB (Admin) ---")
        cmd = "crontab -l"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))

        # 2. Checking for suspicious systemd services
        print("\n--- SYSTEMD (Recent) ---")
        cmd = "ls -lt /etc/systemd/system/ | head -n 20"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))

        # 3. Checking for suspicious cron files
        print("\n--- CRON.D ---")
        cmd = "ls -lt /etc/cron.d/ | head -n 10"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    persistence_hunt()
