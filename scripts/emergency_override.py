import paramiko

def emergency_override():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Emergency Override on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Force recreate everything in one go
        print("Force recreating Postgres and Django...")
        cmd = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose -p hub_prod up -d --force-recreate"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        # 2. Check logs of django immediately
        print("\nChecking Django Logs...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker logs hub_prod_django --tail 20"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    emergency_override()
