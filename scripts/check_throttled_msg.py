import os
import paramiko

def check_throttled_message():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    stdin, stdout, stderr = client.exec_command('docker logs --tail 1000 hub_prod_django')
    logs = stdout.read().decode()
    
    found = False
    for line in logs.splitlines():
        if 'throttled' in line.lower():
            print(line)
            found = True
            
    if not found:
        print("NO THROTTLED MESSAGES FOUND IN LAST 1000 LINES")
            
    client.close()

if __name__ == "__main__":
    check_throttled_message()
