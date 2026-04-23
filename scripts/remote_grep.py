import os
import paramiko

def run_remote():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    stdin, stdout, stderr = client.exec_command('grep -n "postgres-relational" /var/www/och/docker-compose.yml')
    print(stdout.read().decode())
    print(stderr.read().decode())
    client.close()

if __name__ == "__main__":
    run_remote()
