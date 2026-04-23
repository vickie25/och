import paramiko

def identify_database_name():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Identifying Database Name for ID 16384...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # We query the pg_database table to find the name of the populated OID
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v och_postgres_data:/var/lib/postgresql/data postgres:16-alpine sh -c \"sleep 5 && psql -U postgres -d postgres -t -c 'SELECT datname FROM pg_database WHERE oid = 16384' 2>/dev/null || echo 'FAIL'\""
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- DATABASE NAME FOUND ---")
        name = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"Name: {name}")
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    identify_database_name()
