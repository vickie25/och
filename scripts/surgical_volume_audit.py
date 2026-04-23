import paramiko

def surgical_volume_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Surgical Volume Audit (The Search for 55 Users)...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Inspecting the 'och_postgres_data' volume via temporary container
        print("\n--- PROBING: och_postgres_data ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v och_postgres_data:/data alpine du -sh /data"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(f"Size: {stdout.read().decode('utf-8').strip()}")

        # 2. Inspecting the 'hub_prod_postgres_data' volume (the current one)
        print("\n--- PROBING: hub_prod_postgres_data ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v hub_prod_postgres_data:/data alpine du -sh /data"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(f"Size: {stdout.read().decode('utf-8').strip()}")

        # 3. If och_postgres_data exists and is 'heavy', find the DB names inside
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v och_postgres_data:/data alpine ls -R /data/base"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- FOLDER STRUCTURE (Surgical) ---")
        print(stdout.read().decode('utf-8')[:500]) # First 500 chars

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    surgical_volume_audit()
