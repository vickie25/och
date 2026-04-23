import paramiko

def universal_user_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Initiating Universal User Audit across 5 potential volumes...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        vols = ['hub_prod_postgres_data', 'hub_prod_vector_db_data', 'ongozacyberhub_postgres_data', 'ongozacyberhub_vector_db_data', 'och_vector_db_data']
        
        for vol in vols:
            print(f"\n--- AUDITING: {vol} ---")
            # Try both users_user and auth_user
            query = "SELECT COUNT(*) FROM users_user;"
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v {vol}:/var/lib/postgresql/data postgres:16-alpine sh -c \"sleep 4 && psql -U postgres -d ongozacyberhub -t -c '{query}' 2>/dev/null || (psql -U postgres -d ongozacyberhub -t -c 'SELECT COUNT(*) FROM auth_user' 2>/dev/null || echo '0')\""
            
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            result = stdout.read().decode('utf-8', errors='ignore').strip()
            print(f"Result: {result}")
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    universal_user_audit()
