import os
import paramiko

def find_md_docs():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    stdin, stdout, stderr = client.exec_command('find /var/www/och -name "*.md"')
    files = stdout.read().decode().splitlines()
    
    for f in files:
        stdin, stdout, stderr = client.exec_command(f'grep -iE "nginx|502|port" {f}')
        if stdout.read().decode().strip():
            print(f"MATCH FOUND IN: {f}")
            
    client.close()

if __name__ == "__main__":
    find_md_docs()
