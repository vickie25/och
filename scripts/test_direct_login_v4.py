import os
import paramiko

def test_direct_login():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Write login.json inside the container and then curl it
    cmd = """
docker exec -i hub_prod_django bash -c "cat > /tmp/login.json << 'EOF'
{\\\"email\\\": \\\"kelvinmaina202@gmail.com\\\", \\\"password\\\": \\\"os.environ.get('USER_PASSWORD', '')\\\"}
EOF
"
"""
    # Wait, even cat has escaping issues.
    # I'll just use the shell script to verify the user.
    
    # SECOND ATTEMPT: Use python inside the container to do the POST
    python_script = """
import requests
import json
url = 'http://localhost:8000/api/v1/auth/login/'
data = {'email': 'kelvinmaina202@gmail.com', 'password': os.environ.get('USER_PASSWORD', '')}
resp = requests.post(url, json=data)
print(f'STATUS: {resp.status_code}')
print(f'BODY: {resp.text}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python -c \"{python_script}\"")
    
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    test_direct_login()
