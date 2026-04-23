import paramiko

def list_all_tables():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Listing all tables on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # List all tables in the public schema
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec -i hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"\\dt\""
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- TABLE LIST ---")
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    list_all_tables()
