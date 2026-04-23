import paramiko

def definitive_table_list():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Listing ALL tables on the production volume...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Checking och_postgres_data (v16)
        query = "\\dt"
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec -i hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"{query}\""
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- PRODUCTION TABLE LIST ---")
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    definitive_table_list()
