import paramiko

def binary_data_grab():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Binary Data Grab for 55 Users...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Searching the 'och_postgres_data' volume for emails
        print("\n--- SCANNING: och_postgres_data (Searching for '@') ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v och_postgres_data:/data alpine grep -a '@' -r /data | head -n 10"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))

        # 2. Searching specifically for the word 'username' or 'first_name'
        print("\n--- SCANNING: och_postgres_data (Searching for 'username') ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v och_postgres_data:/data alpine grep -a 'username' -r /data | head -n 5"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    binary_data_grab()
