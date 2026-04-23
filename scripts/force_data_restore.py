import paramiko
import time

def force_data_restore():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Force Data Restoration (Final Search for 55 Users)...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Identify the actual service name
        print("Identifying database service name...")
        cmd = "cd /var/www/och && docker-compose ps --services"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        services = stdout.read().decode('utf-8').strip().split('\n')
        db_service = ""
        for s in services:
            if 'db' in s or 'postgres' in s:
                db_service = s
                break
        
        if not db_service:
            db_service = "postgres-relational" # Fallback guess from previous knowledge
        
        print(f"Found database service: {db_service}")

        # 2. Force mapped volumes in docker-compose.yml
        # Switch the current volume to 'och_postgres_data'
        cmd = f"cd /var/www/och && sed -i 's/hub_prod_postgres_data/och_postgres_data/g' docker-compose.yml"
        client.exec_command(cmd, get_pty=True)

        # 3. Force stop the existing container (it might be named differently)
        print("Force-stopping old database containers...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker ps -a --filter name=postgres --format '{{{{.ID}}}}' | xargs -r sudo docker rm -f"
        client.exec_command(cmd, get_pty=True)

        # 4. Restart correctly
        print(f"Restarting {db_service} with 87MB volume...")
        cmd = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose up -d {db_service}"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))

        # 5. Wait for DB to settle
        print("Waiting 20 seconds for database initialization...")
        time.sleep(20)

        # 6. Final Verification: Count the users
        print("\n--- THE FINAL PROOF ---")
        # We'll try a few database names just in case
        dbs_to_try = ["ongozacyberhub", "postgres"]
        for db in dbs_to_try:
            print(f"Checking database '{db}'...")
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_postgres psql -U postgres -d {db} -c 'SELECT count(*) FROM users_user;' 2>/dev/null"
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            result = stdout.read().decode('utf-8').strip()
            if result:
                print(f"USER COUNT ({db}): {result}")

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    force_data_restore()
