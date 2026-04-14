import paramiko

def final_sql_fix():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Manually Align types (Casting director_id to bigint)
        # We also need to check other tables like 'programs_tracks' or similar if they fail.
        print("=== Performing BigInt Type Alignment (SQL) ===")
        sql_command = "ALTER TABLE curriculum_tracks ALTER COLUMN director_id TYPE bigint USING director_id::bigint;"
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker exec ongozacyberhub_postgres psql -U ongoza -d ongozacyberhub -c \"{sql_command}\""
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        # 2. Final Platform Synchronization
        print("\n=== Final Platform Synchronization (Applying ALL) ===")
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py migrate"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        # 3. Final Verification
        print("\n=== Final Migration Status Summary ===")
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py showmigrations"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    final_sql_fix()
