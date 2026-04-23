import os
import paramiko

def set_final_password():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = """
from users.models import User
from django.contrib.auth.models import Group
from users.models import Role, UserRole

email = 'kelvinmaina202@gmail.com'
password = 'OngozaAdmin2026!'

user = User.objects.get(email=email)
user.set_password(password)
user.is_staff = True
user.is_superuser = True
user.account_status = 'active'
user.is_active = True
user.mfa_enabled = False
user.save()

# Ensure it has the Admin role in the UserRole table too
admin_role, _ = Role.objects.get_or_create(name='admin', defaults={'display_name': 'Administrator'})
UserRole.objects.get_or_create(user=user, role=admin_role, defaults={'scope': 'global', 'is_active': True})

print(f'SUCCESS: User {email} updated with password {password}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    set_final_password()
