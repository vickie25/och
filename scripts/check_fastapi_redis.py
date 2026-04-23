import os
import paramiko

def check():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    cmd = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_fastapi cat /app/routers/v1/profiling.py | sed -n '810,825p'"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    print(stdout.read().decode())
    client.close()

if __name__ == "__main__":
    check()
