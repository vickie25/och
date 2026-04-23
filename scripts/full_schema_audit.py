import paramiko

def full_schema_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Full Schema Audit for 55 Users...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. List all databases to explore
        print("\n--- DATABASES ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_postgres psql -U postgres -l"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        db_list_raw = stdout.read().decode('utf-8')
        print(db_list_raw)
        
        db_names = []
        for line in db_list_raw.split('\n'):
            if '|' in line and not line.startswith(' Name') and not line.startswith('---'):
                name = line.split('|')[0].strip()
                if name:
                    db_names.append(name)

        # 2. For each database, list all tables and their row counts
        for db in db_names:
            print(f"\nAUDITING DATABASE: {db}")
            
            # Get table names
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_postgres psql -U postgres -d {db} -t -c \"SELECT tablename FROM pg_tables WHERE schemaname = 'public';\""
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            tables = stdout.read().decode('utf-8').strip().split('\n')
            
            for table in tables:
                table = table.strip()
                if not table: continue
                # Get row count
                cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_postgres psql -U postgres -d {db} -t -c \"SELECT count(*) FROM {table};\""
                stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
                count = stdout.read().decode('utf-8').strip()
                print(f"Table: {table} | Rows: {count}")
                if count == "55":
                    print(f"*** POSSIBLE MATCH FOUND IN {db}.{table} ***")

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    full_schema_audit()
