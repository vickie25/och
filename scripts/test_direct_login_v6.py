import os
import paramiko

def test_direct_login():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    python_script = """
import urllib.request
import json
url = 'http://localhost:8000/api/v1/auth/login/'
data = {'email': 'kelvinmaina202@gmail.com', 'password': os.environ.get('USER_PASSWORD', '')}
req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as f:
        print(f'STATUS: {f.status}')
        print(f'BODY: {f.read().decode()}')
except Exception as e:
    print(f'ERROR: {str(e)}')
    if hasattr(e, 'read'):
        print(f'BODY: {e.read().decode()}')
"""
    # Use a real heredoc
    cmd = f"docker exec -i hub_prod_django python << 'EOF'\n{python_script}\nEOF"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    test_direct_login()
