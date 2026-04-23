import paramiko

def final_data_restore():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Final Data Restoration (Mounting the 87MB Volume)...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Update the docker-compose.yml on the server to use the correct volume
        # We'll use sed to swap the volume name if needed, but let's just push a clean one.
        # Assuming the current compose uses 'hub_prod_postgres_data'
        cmd = f"cd /var/www/och && sed -i 's/hub_prod_postgres_data/och_postgres_data/g' docker-compose.yml"
        print("Switching volumes in docker-compose.yml...")
        client.exec_command(cmd, get_pty=True)

        # 2. Restart the database container
        print("Restarting the Database with the True Volume...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker compose -f /var/www/och/docker-compose.yml up -d postgres"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))

        # 3. Final Verification: Count the users in the newly mounted volume
        # Waiting 5 seconds for DB to initialize
        import time
        time.sleep(10)
        
        print("\n--- THE FINAL PROOF: USER COUNT ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c 'SELECT count(*) FROM users_user;' 2>/dev/null"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        result = stdout.read().decode('utf-8').strip()
        print(f"COUNT: {result}")

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    final_data_restore()
