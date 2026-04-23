import paramiko

def find_users():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(host, username=user, password=password, timeout=120, auth_timeout=120, banner_timeout=120)
        print("Connected.\n")

        container = "hub_prod_postgres"
        db = "ongozacyberhub"

        # 1. List ALL tables in ongozacyberhub (the Django db)
        print(f"=== ALL TABLES IN {db} ===")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec {container} psql -U postgres -d {db} -c '\\dt'"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        # 2. Count rows in each table
        print(f"\n=== ROW COUNTS FOR ALL TABLES IN {db} ===")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec {container} psql -U postgres -d {db} -t -c \"SELECT tablename FROM pg_tables WHERE schemaname = 'public';\""
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        tables_raw = stdout.read().decode('utf-8', 'ignore')
        tables = [t.strip() for t in tables_raw.strip().split('\n') if t.strip()]

        for table in tables:
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec {container} psql -U postgres -d {db} -t -c \"SELECT count(*) FROM {table};\""
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            count = stdout.read().decode('utf-8', 'ignore').strip()
            print(f"  {table}: {count} rows")

        # 3. Count rows in orgs and members
        print(f"\n=== ORGANIZATION DATA ===")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec {container} psql -U postgres -d {db} -c 'SELECT * FROM organization_members;'"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        # 4. Check postgres database - list tables that have the word 'user' in them
        print(f"\n=== TABLES CONTAINING 'user' IN POSTGRES DB ===")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec {container} psql -U postgres -d postgres -t -c \"SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE '%user%';\""
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        user_tables = stdout.read().decode('utf-8', 'ignore')
        print(user_tables)

        # For each user-related table, count rows
        for table in [t.strip() for t in user_tables.strip().split('\n') if t.strip()]:
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec {container} psql -U postgres -d postgres -t -c \"SELECT count(*) FROM {table};\""
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            count = stdout.read().decode('utf-8', 'ignore').strip()
            print(f"  {table}: {count} rows")

        # 5. Check for the 'users' table specifically (with column info)
        print(f"\n=== 'users' TABLE STRUCTURE (postgres db) ===")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec {container} psql -U postgres -d postgres -c '\\d users' 2>/dev/null"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        # 6. Try counting from the 'users' table in postgres db with schema prefix
        print(f"\n=== USER COUNT FROM postgres.public.users ===")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec {container} psql -U postgres -d postgres -t -c 'SELECT count(*) FROM public.users;' 2>/dev/null"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore').strip())

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    find_users()
