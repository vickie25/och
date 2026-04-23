import paramiko

def hit_and_run_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("[AUDIT] Snapping schema info...")
    try:
        client.connect(host, username=user, password=password, timeout=20)
        
        # We target the most likely table mentioned in the model audit
        query = "SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_name IN ('users', 'user_roles', 'sponsor_student_links') AND column_name LIKE '%id%';"
        command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec -i hub_prod_postgres psql -U ongoza -d ongozacyberhub -t -c \"{query}\""
        
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        # Also grab the last 5 Django errors while we are at it
        print("\n[LOGS] Last 5 Django errors:")
        command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker logs hub_prod_django --tail 20"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    hit_and_run_audit()
