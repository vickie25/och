import paramiko

def final_user_count():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Final User Count (The Moment of Closure)...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Checking for the number '55' in every likely user table
        dbs_to_check = ["ongozacyberhub", "postgres"]
        tables_to_check = ["users_user", "auth_user", "users_student"]
        
        found = False
        for db in dbs_to_check:
            for table in tables_to_check:
                cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_postgres psql -U postgres -d {db} -c 'SELECT count(*) FROM {table};' 2>/dev/null"
                stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
                result = stdout.read().decode('utf-8').strip()
                if result and 'count' in result:
                    lines = result.split('\n')
                    count = lines[2].strip() if len(lines) > 2 else "Empty"
                    print(f"DATABASE: {db} | TABLE: {table} | COUNT: {count}")
                    if count != "0" and count != "Empty":
                        found = True

        if not found:
            print("\nWARNING: No users found yet. DB might still be initializing or the volume switch was rejected.")
            # Let's check the volume size again to be sure
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker inspect hub_prod_postgres --format '{{{{ .Mounts }}}}'"
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            print(f"\nCURRENT MOUNT: {stdout.read().decode('utf-8').strip()}")

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    final_user_count()
