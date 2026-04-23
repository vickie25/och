import paramiko

def audit_cohort_schema():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Auditing Cohort Schema on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Check columns for cohorts and curriculum_tracks
        query = "SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_name IN ('cohorts', 'curriculum_tracks', 'enrollments') ORDER BY table_name;"
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec -i hub_prod_postgres psql -U postgres -d ongozacyberhub -t -c \"{query}\""
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- SCHEMA AUDIT ---")
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    audit_cohort_schema()
