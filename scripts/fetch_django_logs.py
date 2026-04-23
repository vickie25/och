import os
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def fetch_django_logs():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    cmd = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker logs hub_prod_fastapi --tail 2000 2>&1 | grep -v '/health' | tail -80"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    output = stdout.read().decode('utf-8', errors='replace')
    # Strip emoji characters that can't be printed
    clean = output.encode('ascii', errors='replace').decode('ascii')
    print(clean)
    
    client.close()

if __name__ == "__main__":
    fetch_django_logs()
