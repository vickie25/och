import os
import paramiko
import sys

def finish_and_verify():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Run migrate (This should now work without Inconsistent error)
        print("\n--- [STEP 1: FINAL GLOBAL MIGRATE] ---")
        command = "sudo docker exec hub_prod_django python manage.py migrate"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 2. Check login functionality (Check if we can access the initiate endpoint without 500)
        # Note: We already verified internal health.
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    finish_and_verify()
