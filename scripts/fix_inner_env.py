import paramiko

def fix_inner_env():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        # We write a pure python script to run on .220 to avoid sed constraints and reliably edit the string
        python_script = """
import os

path = '/var/www/och/backend/django_app/.env'
if os.path.exists(path):
    with open(path, 'r') as f:
        content = f.read()
    content = content.replace('DB_HOST=postgres-relational', 'DB_HOST=38.247.138.250')
    content = content.replace('DB_HOST=postgres', 'DB_HOST=38.247.138.250')
    with open(path, 'w') as f:
        f.write(content)
        
path = '/var/www/och/.env'
if os.path.exists(path):
    with open(path, 'r') as f:
        content = f.read()
    content = content.replace('DB_HOST=postgres-relational', 'DB_HOST=38.247.138.250')
    content = content.replace('DB_HOST=postgres', 'DB_HOST=38.247.138.250')
    with open(path, 'w') as f:
        f.write(content)
"""
        
        c.exec_command(f'echo {password} | sudo -S touch /tmp/fix.py && sudo chmod 777 /tmp/fix.py')
        sftp = c.open_sftp()
        with sftp.open('/tmp/fix.py', 'w') as f:
            f.write(python_script)
        sftp.close()
        
        cmds = [
            f'echo {password} | sudo -S python3 /tmp/fix.py',
            f'cd /var/www/och && echo {password} | sudo -S docker-compose restart django fastapi nextjs',
            f'echo {password} | sudo -S docker exec hub_prod_django env | grep DB_HOST'
        ]
        
        for cmd in cmds:
            stdin, stdout, stderr = c.exec_command(cmd)
            stdout.channel.recv_exit_status()
            print("OUT:", stdout.read().decode('utf-8', 'ignore').strip())
            
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_inner_env()
