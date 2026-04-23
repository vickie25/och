import paramiko
import time

def corrected_data_restore():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Corrected Data Restoration...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Restart using the hyphenated docker-compose command from the project dir
        print("Restarting Database with och_postgres_data volume...")
        cmd = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose up -d postgres"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))

        # 2. Wait for DB to settle
        print("Waiting 15 seconds for database initialization...")
        time.sleep(15)

        # 3. Final Verification: Count the users
        # Checking users_user first
        print("\n--- THE FINAL PROOF ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c 'SELECT count(*) FROM users_user;'"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        result = stdout.read().decode('utf-8').strip()
        print(f"USER COUNT: {result}")

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    corrected_data_restore()
