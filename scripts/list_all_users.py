import os
import paramiko

def list_all_users():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = """
from users.models import User, UserRole

print(f'{"ID":<5} {"EMAIL":<40} {"STATUS":<12} {"SUPERUSER":<10} {"STAFF":<6} {"ACTIVE":<7} {"ROLES":<30}')
print('-' * 120)

for u in User.objects.all().order_by('id'):
    roles = ', '.join([ur.role.name for ur in u.user_roles.filter(is_active=True)]) or 'NONE'
    print(f'{u.id:<5} {u.email:<40} {u.account_status:<12} {str(u.is_superuser):<10} {str(u.is_staff):<6} {str(u.is_active):<7} {roles:<30}')

print(f'\\nTOTAL USERS: {User.objects.count()}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    list_all_users()
