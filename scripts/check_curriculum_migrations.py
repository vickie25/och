import os
import paramiko

def check_migrations():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    cmd = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_django python manage.py showmigrations curriculum"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    print("--- Applied Migrations for 'curriculum' ---")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_migrations()
