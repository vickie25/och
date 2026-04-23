import os
import paramiko
import sys

def apply_migrations_fix():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Apply users migrations with --fake-initial
        print("\n--- [STEP 1: MIGRATING USERS (+FAKE INITIAL)] ---")
        command = "sudo docker exec hub_prod_django python manage.py migrate users --fake-initial"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 2. Apply organizations migrations with --fake-initial
        print("\n--- [STEP 2: MIGRATING ORGANIZATIONS (+FAKE INITIAL)] ---")
        command = "sudo docker exec hub_prod_django python manage.py migrate organizations --fake-initial"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 3. Apply talentscope migrations
        print("\n--- [STEP 3: MIGRATING TALENTSCOPE] ---")
        command = "sudo docker exec hub_prod_django python manage.py migrate talentscope"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 4. Final global migrate pass
        print("\n--- [STEP 4: FINAL GLOBAL MIGRATE PASS] ---")
        command = "sudo docker exec hub_prod_django python manage.py migrate"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    apply_migrations_fix()
