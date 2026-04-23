import os
import paramiko
import sys

def corrective_migration_final():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. DELETE the bad migration record using psql
        print("\n--- [STEP 1: RESETTING MIGRATION STATE] ---")
        sql = "DELETE FROM django_migrations WHERE app='users' AND name='0001_initial';"
        command = f"sudo docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"{sql}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 2. Run migrate --fake-initial
        # This will see 'users' table exists (fake it) but 'user_sessions' is missing (CREATE it)
        print("\n--- [STEP 2: CORRECTIVE MIGRATE --FAKE-INITIAL] ---")
        command = "sudo docker exec hub_prod_django python manage.py migrate users --fake-initial"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 3. Final global migrate
        print("\n--- [STEP 3: GLOBAL MIGRATE] ---")
        command = "sudo docker exec hub_prod_django python manage.py migrate"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 4. FINAL-FINAL VERIFICATION
        print("\n--- [STEP 4: FINAL-FINAL VERIFICATION] ---")
        code = "from users.auth_models import UserSession; print(f'VERIFIED: UserSession Table EXISTS. Count: {UserSession.objects.count()}')"
        command = f"sudo docker exec hub_prod_django python manage.py shell -c \"{code}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    corrective_migration_final()
