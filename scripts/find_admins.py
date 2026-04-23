import os
import paramiko

def find_admins():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    py_cmd = (
        "from django.contrib.auth import get_user_model; "
        "User = get_user_model(); "
        "admins = User.objects.filter(is_superuser=True); "
        "print('Admin Emails: ' + str([u.email for u in admins])); "
    )
    
    cmd = f"docker exec hub_prod_django python manage.py shell -c \"{py_cmd}\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    find_admins()
