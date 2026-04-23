import paramiko

def final_data_unlock():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Final Data Unlock (Relational Data in Vector Volume)...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Checking if och_vector_db_data actually has the users table
        query = "SELECT COUNT(*) FROM users_user;"
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v och_vector_db_data:/var/lib/postgresql/data postgres:16-alpine sh -c \"sleep 5 && psql -U postgres -d ongozacyberhub -t -c '{query}' 2>/dev/null || echo 'FAIL'\""
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- DATA PRESENCE CHECK (Vector Volume) ---")
        result = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"User Count: {result}")
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    final_data_unlock()
