import paramiko

def identify_pg_versions():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    potential_vols = ['och_postgres_data', 'ongoza_postgres_data', 'ongozacyberhub_postgres_data']
    
    print("Reading PG_VERSION files on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        for vol in potential_vols:
            print(f"\n--- VERSION CHECK: {vol} ---")
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' cat /var/lib/docker/volumes/{vol}/_data/PG_VERSION 2>/dev/null || echo 'Missing'"
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            print(f"Version: {stdout.read().decode('utf-8', errors='ignore').strip()}")
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    identify_pg_versions()
