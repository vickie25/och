import paramiko

def final_restoration():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Pull the final repair fixes
        print("=== Pulling Final Migration Repairs ===")
        command = f"cd /var/www/och && git pull origin main"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        # 2. Unblock the drifted Dashboard branch
        print("\n=== Unblocking Dashboard Drift: 0002 (Faking) ===")
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py migrate dashboard 0002_add_profiler_session_id --fake"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
            
        # 3. Final Full Migration (Enforces BigInt Alignment and All Apps)
        print("\n=== Final Synchronization (Applying ALL Pending) ===")
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py migrate"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        # 4. Final Showmigrations Verification
        print("\n=== Final Migration Status Summary ===")
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py showmigrations"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    final_restoration()
