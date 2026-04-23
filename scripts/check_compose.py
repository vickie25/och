import os
import paramiko

def check_compose():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    cmd = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S cat /var/www/och/docker-compose.prod.yml | grep -A 20 fastapi"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    print(stdout.read().decode())
    client.close()

if __name__ == "__main__":
    check_compose()
