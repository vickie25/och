import paramiko

host = "69.30.235.220"
user = "administrator"
password = "Ongoza@#1"

try:
    print("Connecting to host...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=60)
    
    def run_sudo(cmd):
        stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}")
        return stdout.read().decode('utf-8', 'ignore').strip()

    print("\nQuerying external DB directly...")
    # PGPASSWORD=... psql -h 138.197.203.235 -U ongoza_user -d ongozacyberhub -c "SELECT email, is_active, role FROM api_user WHERE email LIKE '%kelvin%';"
    db_cmd = "docker exec hub_prod_postgres sh -c \"PGPASSWORD='ongoza3485cyber758hub434' psql -h 138.197.203.235 -U ongoza_user -d ongozacyberhub -c \\\"SELECT email, is_active, role FROM api_user LIMIT 10;\\\"\""
    print(run_sudo(db_cmd))
    
    print("\nChecking for kelvin specifically...")
    db_cmd_kelvin = "docker exec hub_prod_postgres sh -c \"PGPASSWORD='ongoza3485cyber758hub434' psql -h 138.197.203.235 -U ongoza_user -d ongozacyberhub -c \\\"SELECT email, is_active, role FROM api_user WHERE email LIKE '%kelvin%';\\\"\""
    print(run_sudo(db_cmd_kelvin))
    
    # Check Next.js container logs briefly to see if it stopped throwing fetch failed
    print("\nChecking Next.js logs for fetch failed:")
    print(run_sudo("docker logs --tail 50 hub_prod_nextjs | grep fetch"))

    client.close()
except Exception as e:
    print(f"Error: {e}")
