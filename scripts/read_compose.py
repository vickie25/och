import os
import paramiko
import sys

def read_compose():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [DOCKER COMPOSE DJANGO SECTION] ---")
        command = "sudo cat /var/www/och/docker-compose.yml"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        content = stdout.read().decode('utf-8', 'ignore')
        
        # Find the django service part
        lines = content.splitlines()
        found_django = False
        django_lines = []
        for line in lines:
            if 'django:' in line:
                found_django = True
            if found_django:
                django_lines.append(line)
                if 'fastapi:' in line or 'nginx:' in line: # next services
                    break
        print("\n".join(django_lines))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    read_compose()
