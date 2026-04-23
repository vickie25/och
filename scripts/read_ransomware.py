import paramiko

host = "69.30.235.220"
user = "administrator"
password = "Ongoza@#1"

try:
    print("Reading Ransomware Note...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=60)
    
    def run_sudo(cmd):
        stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}")
        return stdout.read().decode('utf-8', 'ignore').strip()

    # Query local hum_prod_postgres
    print("Tables in readme_to_recover:")
    print(run_sudo("docker exec hub_prod_postgres psql -U postgres -d readme_to_recover -c '\dt'"))

    print("\nReading data from readme_to_recover...")
    print(run_sudo("docker exec hub_prod_postgres psql -U postgres -d readme_to_recover -c \"SELECT * FROM readme_to_recover;\""))
    
    # Also dump exactly what tables exist in ongozacyberhub
    print("\nTables in ongozacyberhub:")
    print(run_sudo("docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c '\dt'"))

    client.close()
except Exception as e:
    print(f"Error: {e}")
