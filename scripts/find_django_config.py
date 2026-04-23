import os
import paramiko
import sys

def find_django_config():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [FINDING DJANGO CONFIG IN COMPOSE] ---")
        command = f'printf "%s\\n" "{password}" | sudo -S -p "" cat /var/www/och/docker-compose.yml'
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        content = stdout.read().decode('utf-8', 'ignore')
        
        in_django = False
        for line in content.splitlines():
            if "django:" in line:
                in_django = True
            if in_django:
                print(line)
                if "image:" in line and "django" not in line and "hub" not in line: # start of next service
                    # Wait, this logic is flawed. Let's just print 50 lines after 'django:'
                    pass
        
        # Better: just find 'django:' index and print 50 lines
        idx = content.find("django:")
        if idx != -1:
            print(content[idx:idx+1500])
        else:
            print("Django not found.")

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    find_django_config()
