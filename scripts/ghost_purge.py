import paramiko

def ghost_purge_and_start():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Ghost Purge on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Kill any process on port 80/443 (The Ghosts)
        print("Clearing ports 80 and 443...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' fuser -k 80/tcp 443/tcp 8000/tcp 2>/dev/null || true"
        client.exec_command(cmd, get_pty=True)
        
        # 2. Stop everything Docker
        print("Stopping all Docker containers...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker stop $(docker ps -aq) 2>/dev/null || true"
        client.exec_command(cmd, get_pty=True)
        
        # 3. Fresh Start with project name 'hub_prod'
        print("Starting production services with project 'hub_prod'...")
        cmd = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose -p hub_prod up -d"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        # We need to wait for the build/start to finish
        print(stdout.read().decode())
        
        client.close()
        print("\nGhost Purge Complete.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    ghost_purge_and_start()
