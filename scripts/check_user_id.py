import os
import paramiko

def check_user_id():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    cmd = 'docker exec hub_prod_django python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); u = User.objects.first(); print(f\'ID: {u.id}, Type: {type(u.id)}\')"'
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_user_id()
