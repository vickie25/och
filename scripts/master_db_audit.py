import paramiko

def master_db_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Master Database Audit for 55 Users...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. List all databases
        print("\n--- MASTER DATABASE LIST ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_postgres psql -U postgres -l"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        db_list = stdout.read().decode('utf-8')
        print(db_list)

        # 2. Extract database names from the list
        # Look for names in the first column
        db_names = []
        for line in db_list.split('\n'):
            if '|' in line and not line.startswith(' Name') and not line.startswith('---'):
                name = line.split('|')[0].strip()
                if name and name not in ['postgres', 'template0', 'template1']:
                    db_names.append(name)
        
        # 3. Probe each database for user tables
        print("\n--- PROBING DATABASES ---")
        for db in db_names:
            print(f"\nChecking database: {db}")
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_postgres psql -U postgres -d {db} -c '\\dt' 2>/dev/null"
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            tables = stdout.read().decode('utf-8')
            if 'users_user' in tables or 'auth_user' in tables:
                print(f"MATCH FOUND in {db}!")
                print(tables)
                # Count the users
                user_table = 'users_user' if 'users_user' in tables else 'auth_user'
                cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_postgres psql -U postgres -d {db} -c 'SELECT count(*) FROM {user_table};' 2>/dev/null"
                stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
                print(f"USER COUNT: {stdout.read().decode('utf-8').strip()}")

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    master_db_audit()
