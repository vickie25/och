import os
import paramiko

def check_nextjs_signup_crash():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    stdin, stdout, stderr = client.exec_command('docker logs --tail 200 hub_prod_nextjs')
    logs = stdout.read().decode('utf-8', errors='ignore')
    
    found = False
    for line in logs.splitlines():
        if 'signup' in line.lower() or ' 500 ' in line or 'error' in line.lower():
            print(line.encode('ascii', 'ignore').decode('ascii'))
            found = True
            
    if not found:
        print("NO SIGNUP ERRORS FOUND IN NEXTJS LOGS")
            
    client.close()

if __name__ == "__main__":
    check_nextjs_signup_crash()
