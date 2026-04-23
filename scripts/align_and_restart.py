import os
import paramiko
import sys

def align_and_restart():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    remote_db = "38.247.138.250"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Update .env to reflect the correct DB_HOST
        print("\n--- [UPDATING .env ON HOST] ---")
        dot_env_path = "/var/www/och/backend/django_app/.env"
        # We ensure DB_HOST is set to the remote one and DB_PASSWORD to postgres
        command = f'sudo sed -i "s/^DB_HOST=.*/DB_HOST={remote_db}/" {dot_env_path} && sudo sed -i "s/^DB_PASSWORD=.*/DB_PASSWORD=postgres/" {dot_env_path}'
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 2. Restart Django to pick up changes
        print("\n--- [RESTARTING DJANGO CONTAINER] ---")
        command = "sudo docker compose -f /var/www/och/docker-compose.yml restart django"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 3. Wait and Verify Connection
        print("\n--- [VERIFYING CONNECTION] ---")
        import time
        time.sleep(5)
        code = "from users.auth_models import UserSession; print(f'CONNECTION SUCCESSFUL: {UserSession.objects.count()} sessions found.')"
        command = f"sudo docker exec hub_prod_django python manage.py shell -c \"{code}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    align_and_restart()
