import paramiko

def run_production_migration():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Running Production Migrations on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Run Django migration
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec -i hub_prod_django python manage.py migrate --noinput"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        
        print("\n--- MIGRATION OUTPUT ---")
        output = stdout.read().decode('utf-8', errors='ignore')
        print(output)
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    run_production_migration()
