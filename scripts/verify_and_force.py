import paramiko
import sys

def verify_and_force():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    remote_db = "38.247.138.250"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [VERIFYING docker-compose.yml HOST SETTING] ---")
        command = "grep -C 5 \"DB_HOST\" /var/www/och/docker-compose.yml"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 1. FORCE THE CHANGE (Delete and Recreate)
        print("\n--- [FORCING CONFIG RELOAD (DOWN & UP)] ---")
        command = "sudo docker compose -f /var/www/och/docker-compose.yml down django && sudo docker compose -f /var/www/och/docker-compose.yml up -d django"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 2. VERIFY RUNTIME AGAIN
        print("\n--- [FINAL RUNTIME CHECK] ---")
        import time
        time.sleep(10)
        code = "import os; print(f'RUNTIME DB_HOST: {os.environ.get(\"DB_HOST\")}')"
        command = f"sudo docker exec hub_prod_django python manage.py shell -c \"{code}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    verify_and_force()
