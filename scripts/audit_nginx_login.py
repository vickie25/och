import os
import paramiko

def audit_nginx_login():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Check for ANY POST request from the user's IP
    user_ip = '41.204.187.5'
    stdin, stdout, stderr = client.exec_command(f'docker logs --tail 500 hub_prod_nginx')
    logs = stdout.read().decode('utf-8', errors='ignore')
    
    found = False
    for line in logs.splitlines():
        if user_ip in line and 'POST' in line:
            print(line)
            found = True
            
    if not found:
        print(f"NO POST REQUESTS FOUND FROM {user_ip} IN LAST 500 LINES")
            
    client.close()

if __name__ == "__main__":
    audit_nginx_login()
