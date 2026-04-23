import os
import paramiko
import sys

def check_callback_error():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Search Django logs for callback errors and tracebacks
        print("\n--- [DJANGO LOGS: SEARCHING FOR CALLBACK ERRORS] ---")
        command = "sudo docker logs hub_prod_django 2>&1 | grep -C 20 'callback'"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        print("\n--- [DJANGO LOGS: SEARCHING FOR TRACEBACKS] ---")
        command = "sudo docker logs hub_prod_django 2>&1 | tail -n 200"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 2. Check the Role table to ensure roles exist
        print("\n--- [CHECKING ROLES IN DB] ---")
        command = "sudo docker exec hub_prod_django python manage.py shell -c 'from users.models import Role; print(list(Role.objects.values_list(\"name\", flat=True)))'"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_callback_error()
