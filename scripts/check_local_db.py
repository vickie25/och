import paramiko

host = "69.30.235.220"
user = "administrator"
password = "Ongoza@#1"

try:
    print("Checking Local DB for users...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=60)
    
    def run_sudo(cmd):
        stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}")
        return stdout.read().decode('utf-8', 'ignore').strip()

    # Query local hub_prod_postgres
    # List databases
    print("Databases in local Postgres:")
    print(run_sudo("docker exec hub_prod_postgres psql -U postgres -c '\\l'"))

    print("\nLooking for kelvin in ongozacyberhub...")
    print(run_sudo("docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"SELECT email, role FROM api_user WHERE email LIKE '%kelvin%';\""))

    print("\nCounting users in ongozacyberhub...")
    print(run_sudo("docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"SELECT count(*) FROM api_user;\""))
    
    print("\nChecking if there's any other database with data...")
    dbs = ["postgres", "ongozacyberhub"]
    for db in dbs:
         print(f"Users in {db}:")
         print(run_sudo(f"docker exec hub_prod_postgres psql -U postgres -d {db} -c \"SELECT count(*) FROM api_user;\""))

    client.close()
except Exception as e:
    print(f"Error: {e}")
