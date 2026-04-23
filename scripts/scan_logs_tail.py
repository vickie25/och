import os
import paramiko
import sys

def scan_logs_tail():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    stdin, stdout, stderr = client.exec_command('docker logs --tail 100 hub_prod_nextjs')
    
    logs_bytes = stdout.read()
    sys.stdout.buffer.write(logs_bytes)
    
    client.close()

if __name__ == "__main__":
    scan_logs_tail()
