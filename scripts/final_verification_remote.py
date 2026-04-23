import paramiko
import sys

def final_verification_remote():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [FINAL VERIFICATION: REMOTE DB THROUGH DJANGO] ---")
        # Fixed the shell command quoting
        code = "import os; from users.auth_models import UserSession; print(f'VERIFIED: DB_HOST={os.environ.get(\"DB_HOST\")}. UserSession Count={UserSession.objects.count()}')"
        command = f"sudo docker exec hub_prod_django python manage.py shell -c \"{code}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    final_verification_remote()
