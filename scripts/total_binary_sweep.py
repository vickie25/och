import paramiko

def total_binary_sweep():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Total Binary Sweep for 55 Users...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Exhaustive binary search for any email address using 'strings'
        # We search /data/base which is where Postgres keeps table files
        print("\n--- SEARCHING FOR EMAIL SIGNATURES (Total Sweep) ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v och_postgres_data:/data alpine find /data/base -type f -exec strings {{}} \\; | grep '@' | head -n 20"
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        # 2. Search for the string 'Ongoza' - likely in your user profiles
        print("\n--- SEARCHING FOR 'Ongoza' ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v och_postgres_data:/data alpine find /data/base -type f -exec strings {{}} \\; | grep -i 'Ongoza' | head -n 5"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    total_binary_sweep()
