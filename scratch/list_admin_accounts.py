import paramiko
import time

def fix_admin_and_check_mfa():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("=== ALL ADMIN/SUPERUSER ACCOUNTS ===")
        command = f"""printf '%s\\n' '{password}' | sudo -S -p '' docker exec ongozacyberhub_django python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()
from users.models import User
from users.auth_models import MFAMethod

# All superusers
supers = User.objects.filter(is_superuser=True)
print('--- Superusers ---')
for u in supers:
    print(f'  email={{u.email}} | status={{u.account_status}} | mfa_enabled={{u.mfa_enabled}} | mfa_method={{u.mfa_method}}')

# All admin-role users
from users.models import UserRole
admin_roles = UserRole.objects.filter(role__name='admin', is_active=True).select_related('user', 'role')
print('--- Admin Role Users ---')
for ur in admin_roles:
    u = ur.user
    methods = MFAMethod.objects.filter(user=u)
    method_str = ', '.join([f'{{m.method_type}}(enabled={{m.enabled}})' for m in methods]) or 'none'
    print(f'  email={{u.email}} | status={{u.account_status}} | mfa_enabled={{u.mfa_enabled}} | methods={{method_str}}')
"
"""
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        time.sleep(6)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    fix_admin_and_check_mfa()
