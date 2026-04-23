import os
import paramiko
import json

def test_direct_login():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    payload = {
        "email": "kelvinmaina202@gmail.com",
        "password": os.environ.get('USER_PASSWORD', '')
    }
    # Be careful with escaping for the shell
    payload_str = json.dumps(payload).replace('"', '\\"')
    
    cmd = f"docker exec hub_prod_django curl -i -X POST http://localhost:8000/api/v1/auth/login/ -H 'Content-Type: application/json' -d '{payload_str}'"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    print("--- STDOUT ---")
    print(stdout.read().decode())
    print("--- STDERR ---")
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    test_direct_login()
