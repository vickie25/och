import paramiko

def internal_env_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Internal Environment Audit...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Checking the environment variables of the running Django container
        print("\n--- RUNNING DJANGO ENVIRONMENT ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_django env | grep DB_"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))

        # 2. Reading the .env file from the source directory on the server
        print("\n--- SOURCE .env FILE ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' cat /var/www/och/backend/django_app/.env"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    internal_env_audit()
