import os
import paramiko

def fetch_logs():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    cmd = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker logs --tail 100 hub_prod_fastapi"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    print("--- STDOUT ---")
    print(stdout.read().decode())
    
    print("--- STDERR ---")
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    fetch_logs()
