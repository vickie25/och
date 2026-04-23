import os
import paramiko

def find_ai_coach_error():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    stdin, stdout, stderr = client.exec_command('docker logs --tail 500 hub_prod_django')
    logs = stdout.read().decode()
    
    for line in logs.splitlines():
        if 'AI Coach error' in line:
            print(line)
        if 'Internal Server Error' in line:
            print(line)
            
    client.close()

if __name__ == "__main__":
    find_ai_coach_error()
