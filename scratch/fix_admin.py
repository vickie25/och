import paramiko
import time

def fix_admin():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # Use django manage.py shell -c approach instead
        script = """
from users.models import User, UserRole
from users.auth_models import MFAMethod

supers = User.objects.filter(is_superuser=True)
print('SUPERUSERS:')
for u in supers:
    print(u.email, '|', u.account_status, '| mfa_enabled:', u.mfa_enabled)

print('ADMIN ROLE USERS:')
for ur in UserRole.objects.filter(role__name='admin', is_active=True).select_related('user'):
    u = ur.user
    print(u.email, '|', u.account_status, '| mfa_enabled:', u.mfa_enabled, '| mfa_method:', u.mfa_method)
"""
        sftp = client.open_sftp()
        with sftp.file('/tmp/check_admins.py', 'w') as f:
            f.write(script)
        sftp.close()
        
        print("=== ADMIN ACCOUNTS ===")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec -w /app ongozacyberhub_django python manage.py shell < /tmp/check_admins.py"
        
        # Copy the file INTO the container
        cmd1 = f"printf '%s\\n' '{password}' | sudo -S -p '' docker cp /tmp/check_admins.py ongozacyberhub_django:/tmp/check_admins.py"
        stdin1, stdout1, stderr1 = client.exec_command(cmd1, get_pty=True)
        time.sleep(3)
        
        # Run with manage.py shell
        cmd2 = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec -w /app ongozacyberhub_django python manage.py shell < /tmp/check_admins.py 2>&1"
        stdin2, stdout2, stderr2 = client.exec_command(cmd2, get_pty=True)
        time.sleep(8)
        output = stdout2.read().decode()
        print(output)
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    fix_admin()
