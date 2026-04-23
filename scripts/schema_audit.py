import paramiko

def schema_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("[PHASE 2: AUDIT] Connecting to server...")
    client.connect(host, username=user, password=password, timeout=30)

    def run_sql(query, label):
        print(f"\n--- {label} ---")
        # -t means tuples only (no headers)
        command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec -i hub_prod_postgres psql -U ongoza -d ongozacyberhub -t -c \"{query}\""
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        output = stdout.read().decode()
        print(output)
        return output

    # 1. Start Postgres (if not running) to perform the audit
    print("Ensuring Postgres is running...")
    client.exec_command(f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose up -d postgres-relational", get_pty=True)
    import time
    time.sleep(5)

    # 2. Audit Foreign Keys and Types for suspected tables
    queries = {
        "Users Table": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users';",
        "Cohort Enrollments": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'programs_enrollment';",
        "Curriculum Tracks": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'curriculum_tracks';",
        "Device Trust": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users_devicetrust';"
    }

    for label, query in queries.items():
        run_sql(query, label)

    # 3. Pull latest Django logs to confirm the error message (Wait for django to try and start)
    print("\nAttempting to start Django for log capture...")
    client.exec_command(f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose up -d django", get_pty=True)
    time.sleep(10)
    
    print("\n--- Django Error Logs ---")
    command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker logs hub_prod_django --tail 50"
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    schema_audit()
