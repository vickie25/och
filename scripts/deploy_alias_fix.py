import paramiko

def deploy_alias_fix():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Deploying Final Alias Fix on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. We must push the local docker-compose.yml to the server
        # Since I cannot use SCP easily, I will use a clever cat-to-file trick
        print("Pushing updated docker-compose.yml to server...")
        with open('docker-compose.yml', 'r') as f:
            content = f.read()
        
        # Escape single quotes for the echo command
        escaped_content = content.replace("'", "'\\''")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' sh -c \"printf '%s' '{escaped_content}' > /var/www/och/docker-compose.yml\""
        client.exec_command(cmd, get_pty=True)

        # 2. Down and Up
        print("Restarting stack with new network aliases...")
        cmd = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose -p hub_prod down && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose -p hub_prod up -d"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        # 3. Force Nginx reload just in case
        print("Finalizing Nginx...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_nginx nginx -s reload"
        client.exec_command(cmd, get_pty=True)
        
        client.close()
        print("\nDeployment Complete.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    deploy_alias_fix()
