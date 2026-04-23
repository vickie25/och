import os
import paramiko

def check_500_errors():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    stdin, stdout, stderr = client.exec_command('docker logs --tail 200 hub_prod_django')
    logs = stdout.read().decode()
    
    errors = [line for line in logs.splitlines() if ' 500 ' in line]
    
    if errors:
        print("FOUND 500 ERRORS:")
        for err in errors:
            print(err)
    else:
        print("No 500 errors found in the last 200 lines.")
            
    client.close()

if __name__ == "__main__":
    check_500_errors()
