import os
import paramiko

def check_nextjs_logs():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    stdin, stdout, stderr = client.exec_command('docker logs --tail 200 hub_prod_nextjs')
    # Use utf-8 and ignore errors
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)
    
    client.close()

if __name__ == "__main__":
    check_nextjs_logs()
