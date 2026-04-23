import os
import paramiko

def find_traceback():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    stdin, stdout, stderr = client.exec_command('docker logs --tail 1000 hub_prod_django')
    logs = stdout.read().decode()
    
    found = False
    for line in logs.splitlines():
        if 'Traceback' in line or found:
            print(line)
            found = True
            if 'Error' in line and not line.endswith(':'):
                found = False # Stop after the error message line
            
    client.close()

if __name__ == "__main__":
    find_traceback()
