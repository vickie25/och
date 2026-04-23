import os
import paramiko
import sys

def kickstart_and_migrate():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Manual SQL Kickstart to satisfy 'admin' dependency
        print("\n--- [STEP 1: SQL KICKSTART] ---")
        sql_commands = [
            "INSERT INTO django_migrations (app, name, applied) VALUES ('users', '0001_initial', NOW()) ON CONFLICT (app, name) DO NOTHING;",
            "INSERT INTO django_migrations (app, name, applied) VALUES ('organizations', '0001_initial', NOW()) ON CONFLICT (app, name) DO NOTHING;"
        ]
        for sql in sql_commands:
            print(f"Executing: {sql}")
            command = f"sudo docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"{sql}\""
            stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
            print(stdout.read().decode('utf-8', 'ignore'))
        
        # 2. Run real migrations for users (this should now work)
        print("\n--- [STEP 2: MIGRATING USERS] ---")
        command = "sudo docker exec hub_prod_django python manage.py migrate users"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 3. Run all remaining migrations
        print("\n--- [STEP 3: FINAL GLOBAL MIGRATE] ---")
        command = "sudo docker exec hub_prod_django python manage.py migrate"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 4. Final verification of UserSession
        print("\n--- [STEP 4: FINAL VERIFICATION] ---")
        code = "from users.auth_models import UserSession; print(f'VERIFIED: UserSession table present. Count: {UserSession.objects.count()}')"
        command = f"sudo docker exec hub_prod_django python manage.py shell -c \"{code}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    kickstart_and_migrate()
