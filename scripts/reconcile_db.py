import paramiko

def reconcile_db():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Merge migrations in 'users' app
        print("=== Merging Conflicting Migrations in 'users' app ===")
        # We use --noinput to handle it non-interactively
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py makemigrations --merge --noinput"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        # 2. Apply all migrations
        print("\n=== Applying ALL Pending Migrations (including BigInt alignment) ===")
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py migrate"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        # 3. Final Verification
        print("\n=== Final Migration Status ===")
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py showmigrations"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    reconcile_db()
