import paramiko

def reconcile_all():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Merge migrations in 'users' app
        print("=== Merging 'users' app branches ===")
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py makemigrations users --merge --noinput"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        # 2. Merge migrations in 'curriculum' app
        print("\n=== Merging 'curriculum' app branches ===")
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py makemigrations curriculum --merge --noinput"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        # 3. Unblock ALL drifted Curriculum migrations in Path A
        # Based on the errors, Path A is already in the DB.
        fakes = [
            "0005_curriculumtrack_tier2_completion_config",
            "0006_beginner_track_requirements",
            "0007_tier3_completion_config",
            "0011_tier4_completion_config",
            "0012_tier5_completion_config"
        ]
        
        for migration in fakes:
            print(f"\n=== Unblocking '{migration}' (Faking) ===")
            command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py migrate curriculum {migration} --fake"
            stdin, stdout, stderr = client.exec_command(command, get_pty=True)
            print(stdout.read().decode())
        
        # 4. Final Synchronization
        print("\n=== Final Synchronization (Applying ALL) ===")
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py migrate"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        # 5. Final Audit
        print("\n=== Final Migration Status ===")
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py showmigrations"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    reconcile_all()
