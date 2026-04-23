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
    json_payload = json.dumps(payload).replace('"', '\\"')
    
    cmd = f'docker exec hub_prod_django curl -s -X POST http://localhost:8000/api/v1/auth/login/ -H "Content-Type: application/json" -d "{json_payload}"'
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    test_direct_login()
