import paramiko

def final_strike():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Final Strike on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Targeted removal of the conflicting container
        print("Force removing conflicting postgres container...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker rm -f hub_prod_postgres 2>/dev/null || true"
        client.exec_command(cmd, get_pty=True)
        
        # 2. Final attempt to launch the stack
        print("Launching production stack (hub_prod)...")
        cmd = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose -p hub_prod up -d"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        # We wait for it to finish
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        # 3. Quick check of running containers
        print("\nChecking final status...")
        cmd = f"docker ps --format 'table {{.Names}}\\t{{.Status}}'"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
        print("\nFinal Strike Complete.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    final_strike()
