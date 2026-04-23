import os
import paramiko

def audit_user_roles():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = """
from users.models import User, UserRole, Role

email = 'kelvinmaina202@gmail.com'
user = User.objects.get(email=email)
roles = UserRole.objects.filter(user=user)

print(f'USER_ID: {user.id}')
print(f'IS_SUPERUSER: {user.is_superuser}')
print(f'IS_STAFF: {user.is_staff}')

if not roles.exists():
    print('ROLES: NONE FOUND')
else:
    for ur in roles:
        print(f'ROLE_NAME: {ur.role.name} | SCOPE: {ur.scope} | ACTIVE: {ur.is_active}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    audit_user_roles()
