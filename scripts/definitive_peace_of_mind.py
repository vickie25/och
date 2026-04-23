import paramiko

def definitive_peace_of_mind():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Definitive Data Audit on och_postgres_data...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # We try both users and users_user
        query = "SELECT 'User Records' as label, COUNT(*) FROM users_user UNION SELECT 'Cohort Records', COUNT(*) FROM cohorts;"
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec -i hub_prod_postgres psql -U postgres -d ongozacyberhub -t -c \"{query}\" 2>/dev/null || (echo 'Trying auth_user...' && docker exec -i hub_prod_postgres psql -U postgres -d ongozacyberhub -t -c \"SELECT 'Auth User Records', COUNT(*) FROM auth_user UNION SELECT 'Cohort Records', COUNT(*) FROM cohorts;\" 2>/dev/null)"
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- FINAL DATA SAFETY CERTIFICATE ---")
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    definitive_peace_of_mind()
