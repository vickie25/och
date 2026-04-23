import paramiko

def database_name_discovery():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    potential_vols = ['och_postgres_data', 'ongoza_postgres_data', 'ongozacyberhub_postgres_data']
    
    print("Discovering database names on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        for vol in potential_vols:
            print(f"\n--- DB LIST: {vol} ---")
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v {vol}:/var/lib/postgresql/data postgres:15-alpine sh -c \"sleep 4 && psql -U postgres -l 2>/dev/null || echo 'No Databases'\""
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            print(stdout.read().decode('utf-8', errors='ignore'))
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    database_name_discovery()
