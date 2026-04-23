import os
import paramiko

def check_rbac():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Check roles only
    py_cmd = (
        "from users.models import UserRole; "
        "roles = UserRole.objects.filter(user_id=13); "
        "print('Roles: ' + str([r.role.name for r in roles])); "
    )
    
    cmd = f"docker exec hub_prod_django python manage.py shell -c \"{py_cmd}\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_rbac()
