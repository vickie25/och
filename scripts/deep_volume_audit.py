import paramiko
import json

def deep_volume_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Deep Volume Audit for 55 Users...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Inspect the running database to find the volume
        cmd = "docker inspect hub_prod_postgres"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        inspect_data = stdout.read().decode('utf-8')
        print("\n--- DATABASE MOUNTS ---")
        try:
            data = json.loads(inspect_data)
            mounts = data[0].get('Mounts', [])
            for mount in mounts:
                print(f"Source: {mount['Source']} -> Destination: {mount['Destination']}")
        except:
            print("Failed to parse docker inspect output.")

        # 2. List all tables in the current project database
        print("\n--- PROJECT TABLES ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c '\\dt'"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))

        # 3. Exhaustive search for the '55' number across likely user tables
        print("\n--- TABLE RECORD COUNTS (Seeking 55) ---")
        tables_to_check = ["users_user", "auth_user", "users_customuser", "users_student", "core_user"]
        for table in tables_to_check:
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c 'SELECT count(*) FROM {table};' 2>/dev/null"
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            res = stdout.read().decode('utf-8').strip()
            if res:
                print(f"{table}: {res}")

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    deep_volume_audit()
