import os
import paramiko
import sys

def check_profiler_services():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [DOCKER SERVICES STATUS] ---")
        command = "sudo docker ps"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        print("\n--- [NGINX ROUTING CHECK] ---")
        # Check nginx for profiling route
        command = "sudo grep -r 'profiling' /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ /var/www/och/backend/docker/nginx.conf 2>/dev/null"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_profiler_services()
