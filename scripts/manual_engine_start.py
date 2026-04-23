import paramiko

def manual_engine_start():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Manually Restarting Django Engine on Server...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # We need to find the dir with docker-compose.yml
        # Assuming it's in /var/www/och
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker start hub_prod_django"
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))
        
        # Now verify it's up
        cmd = "docker ps -a --filter name=hub_prod_django"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8'))

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    manual_engine_start()
