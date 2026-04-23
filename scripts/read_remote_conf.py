import os
import paramiko

def read_remote_file(path):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    stdin, stdout, stderr = client.exec_command(f'cat {path}')
    content = stdout.read().decode('utf-8', errors='ignore')
    print(content.encode('ascii', 'ignore').decode('ascii'))
    
    client.close()

if __name__ == "__main__":
    read_remote_file('/var/www/och/nginx/conf.d-local/ssl.conf')
