import paramiko

def sql_restoration():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        sql_commands = [
            "ALTER TABLE tracks ADD COLUMN IF NOT EXISTS director_id_backup VARCHAR(36);",
            "UPDATE tracks SET director_id_backup = director_id;",
            "UPDATE tracks SET director_id = NULL;",
            "ALTER TABLE tracks ALTER COLUMN director_id TYPE BIGINT USING director_id::bigint;"
        ]
        
        print("=== Executing Data-Safe BigInt Restoration (SQL) ===")
        for sql in sql_commands:
            print(f"Running: {sql}")
            command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker exec ongozacyberhub_postgres psql -U ongoza -d ongozacyberhub -c \"{sql}\""
            stdin, stdout, stderr = client.exec_command(command, get_pty=True)
            print(stdout.read().decode())
            
        print("\n=== Final Platform Synchronization ===")
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py migrate"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    sql_restoration()
