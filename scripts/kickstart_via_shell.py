import os
import paramiko
import sys

def kickstart_via_shell():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Insert migration records via Django Shell (guaranteed correct DB)
        print("\n--- [STEP 1: SHELL KICKSTART] ---")
        code = """
from django.db import connection
try:
    with connection.cursor() as cursor:
        # Check if record exists
        cursor.execute("SELECT 1 FROM django_migrations WHERE app='users' AND name='0001_initial'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('users', '0001_initial', NOW())")
            print("INSERTED users.0001_initial")
        
        cursor.execute("SELECT 1 FROM django_migrations WHERE app='organizations' AND name='0001_initial'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('organizations', '0001_initial', NOW())")
            print("INSERTED organizations.0001_initial")
except Exception as e:
    print(f'ERROR: {str(e)}')
"""
        command = f"sudo docker exec hub_prod_django python manage.py shell -c \"{code}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 2. Try migrate users again
        print("\n--- [STEP 2: MIGRATING USERS] ---")
        command = "sudo docker exec hub_prod_django python manage.py migrate users"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 3. Final global migrate
        print("\n--- [STEP 3: GLOBAL MIGRATE] ---")
        command = "sudo docker exec hub_prod_django python manage.py migrate"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    kickstart_via_shell()
