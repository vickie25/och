import os
import paramiko

def make_director():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = """
from users.models import User, UserRole, Role

u = User.objects.get(email='kelvin.reallife8@gmail.com')
u.set_password('OngozaAdmin2026!')
u.is_staff = True
u.is_active = True
u.account_status = 'active'
u.profiling_complete = True
u.mfa_enabled = False
u.email_verified = True
u.save()

# Remove any existing roles
u.user_roles.all().delete()

# Add program_director role
role, _ = Role.objects.get_or_create(name='program_director', defaults={'display_name': 'Program Director'})
UserRole.objects.create(user=u, role=role, scope='global', is_active=True)

# Add to MFA exempt
from django.conf import settings
exempt = getattr(settings, 'MFA_EXEMPT_EMAILS', [])
if u.email.lower() not in exempt:
    exempt.append(u.email.lower())

# Verify
roles = [ur.role.name for ur in u.user_roles.filter(is_active=True)]
print(f'DONE: {u.email} (ID {u.id})')
print(f'  Roles: {roles}')
print(f'  Status: {u.account_status}')
print(f'  MFA: {u.mfa_enabled}')
print(f'  Profiling: {u.profiling_complete}')
print(f'  Password: OngozaAdmin2026!')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    client.close()

if __name__ == "__main__":
    make_director()
