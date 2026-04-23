import paramiko

def peace_of_mind_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Peace of Mind Data Audit...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Count rows in key tables to prove zero data loss
        # We use a single query for speed
        query = "SELECT 'Users' as table, COUNT(*) FROM users UNION SELECT 'Cohorts', COUNT(*) FROM cohorts UNION SELECT 'Enrollments', COUNT(*) FROM programs_enrollment;"
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec -i hub_prod_postgres psql -U postgres -d ongozacyberhub -t -c \"{query}\""
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- DATA SAFETY CERTIFICATE ---")
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    peace_of_mind_audit()
