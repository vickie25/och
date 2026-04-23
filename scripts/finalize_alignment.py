import os
import paramiko
import sys

def finalize_alignment():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    remote_db = "38.247.138.250"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Update docker-compose.yml (Modify DB_HOST override)
        print("\n--- [UPDATING docker-compose.yml] ---")
        compose_path = "/var/www/och/docker-compose.yml"
        # We replace any line that has DB_HOST: postgres-relational with DB_HOST: 38.247.138.250
        command = f'sudo sed -i "s/DB_HOST: postgres-relational/DB_HOST: {remote_db}/g" {compose_path}'
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 2. Re-verify .env for good measure
        dot_env_path = "/var/www/och/backend/django_app/.env"
        command = f'sudo sed -i "s/^DB_HOST=.*/DB_HOST={remote_db}/" {dot_env_path}'
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print("Updated .env")
        
        # 3. Pull and Up to apply changes effectively (or just restart)
        # We'll use docker-compose up -d to pick up the yaml changes
        print("\n--- [REPLICATING CONFIG CHANGES TO RUNTIME] ---")
        command = "sudo docker compose -f /var/www/och/docker-compose.yml up -d django"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 4. FINAL VERIFICATION
        print("\n--- [FINAL SMOKE TEST: RUNTIME CONNECTIVITY] ---")
        import time
        time.sleep(10) # wait for startup
        code = "from users.auth_models import UserSession; print(f'RUNTIME SUCCESS: Remote DB Connected. Session Count: {UserSession.objects.count()}')"
        command = f"sudo docker exec hub_prod_django python manage.py shell -c \"{code}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    finalize_alignment()
