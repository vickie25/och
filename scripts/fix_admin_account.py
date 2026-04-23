import os
import paramiko

def fix_admin_user():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Python script to fix the user
    script = """
from django.contrib.auth import get_user_model
User = get_user_model()
email = 'kelvinmaina202@gmail.com'
try:
    u = User.objects.get(email=email)
    u.is_superuser = True
    u.is_staff = True
    u.is_active = True
    u.email_verified = True
    u.account_status = 'active'
    u.mfa_enabled = False
    u.set_password(os.environ.get('USER_PASSWORD', ''))
    u.save()
    print(f'SUCCESS: User {email} updated and password set.')
except User.DoesNotExist:
    u = User.objects.create_superuser(email=email, username=email, password=os.environ.get('USER_PASSWORD', ''))
    u.email_verified = True
    u.account_status = 'active'
    u.mfa_enabled = False
    u.save()
    print(f'SUCCESS: Superuser {email} created.')
"""
    # Write script to a temporary file in the container
    client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    
    # Verify
    stdin, stdout, stderr = client.exec_command("docker exec hub_prod_django python manage.py shell -c \"from django.contrib.auth import get_user_model; u = get_user_model().objects.get(email='kelvinmaina202@gmail.com'); print(f'User: {u.email}, Super: {u.is_superuser}, MFA: {u.mfa_enabled}')\"")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    fix_admin_user()
