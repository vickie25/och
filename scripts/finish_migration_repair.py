import os
import paramiko
import sys

def finish_migration_repair():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Organizations kickstart
        print("\n--- [STEP 1: ORGANIZATIONS KICKSTART] ---")
        sql = "INSERT INTO django_migrations (app, name, applied) VALUES ('organizations', '0001_initial', '2026-04-10 00:00:00+00') ON CONFLICT (app, name) DO NOTHING;"
        command = f"sudo docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"{sql}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 2. Migrate Users
        print("\n--- [STEP 2: MIGRATING USERS] ---")
        command = "sudo docker exec hub_prod_django python manage.py migrate users"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 3. Global Migrate
        print("\n--- [STEP 3: GLOBAL MIGRATE] ---")
        command = "sudo docker exec hub_prod_django python manage.py migrate"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 4. Final verification
        print("\n--- [STEP 4: FINAL VERIFICATION] ---")
        code = "from users.auth_models import UserSession; print(f'SUCCESS: UserSession Count: {UserSession.objects.count()}')"
        command = f"sudo docker exec hub_prod_django python manage.py shell -c \"{code}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    finish_migration_repair()
