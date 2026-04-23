import paramiko

def final_engine_rescue():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Final Engine Rescue on Server...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. List ALL containers to find the django one
        cmd = "docker ps -a --format '{{.Names}} {{.Status}}'"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        containers = stdout.read().decode('utf-8')
        print(f"All Containers:\n{containers}")
        
        # 2. Force start if it exists, or run from compose
        # We know its probably och-django-1 or hub_prod_django
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker restart hub_prod_django || (cd /var/www/och && sudo docker compose up -d django)"
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))
        
        # 3. Final verification
        cmd = "docker ps --filter name=django"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- RESCUED ENGINE STATUS ---")
        print(stdout.read().decode('utf-8'))

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    final_engine_rescue()
