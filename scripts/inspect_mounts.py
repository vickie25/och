import os
import paramiko
import json

def inspect_mounts():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    stdin, stdout, stderr = client.exec_command("docker inspect hub_prod_nginx --format '{{json .Mounts}}'")
    out = stdout.read().decode()
    print(out)
    client.close()

if __name__ == "__main__":
    inspect_mounts()
