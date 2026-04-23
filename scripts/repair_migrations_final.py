import os
import paramiko
import sys

def apply_migrations_repair():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Fake the initial migrations for apps that already have tables but missing history
        # This resolves the InconsistentMigrationHistory error.
        print("\n--- [STEP 1: FAKING INITIAL HISTORY] ---")
        apps_to_fake = ['users', 'organizations', 'talentscope', 'core', 'knowledge']
        for app in apps_to_fake:
            print(f"Faking {app} 0001...")
            command = f"sudo docker exec hub_prod_django python manage.py migrate {app} 0001 --fake"
            stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
            print(stdout.read().decode('utf-8', 'ignore'))
        
        # 2. Now run the full migrate to create the MISSING tables (like user_sessions)
        print("\n--- [STEP 2: RUNNING REAL MIGRATIONS] ---")
        command = "sudo docker exec hub_prod_django python manage.py migrate"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 3. Verify specifically that UserSession table now exists
        print("\n--- [STEP 3: VERIFYING USERSESSION TABLE] ---")
        code = "from users.auth_models import UserSession; print(f'UserSession Table Exists. Count: {UserSession.objects.count()}')"
        command = f"sudo docker exec hub_prod_django python manage.py shell -c \"{code}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    apply_migrations_repair()
