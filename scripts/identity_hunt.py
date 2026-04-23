import paramiko

def identity_hunt():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    email_to_find = "cresdynamics@gmail.com"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Executing Identity Hunt for '{email_to_find}'...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Searching for the email in the raw bytes of the 87MB volume
        print("\n--- SEARCHING FOR YOUR IDENTITY ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v och_postgres_data:/data alpine grep -a '{email_to_find}' -r /data"
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        result = stdout.read().decode('utf-8', 'ignore')
        if result:
            print(f"IDENTITY MATCH FOUND!")
            print(result[:500]) # Show the row content
        else:
            print("No identity found in 'och_postgres_data'.")
            
        # 2. Searching other volumes just in case
        print("\n--- SCANNING ALL VOLUMES FOR YOUR IDENTITY ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' grep -a '{email_to_find}' -r /var/lib/docker/volumes/ | head -n 5"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    identity_hunt()
