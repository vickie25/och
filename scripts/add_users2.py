import paramiko

script = """
import os
import django
from django.conf import settings

# Setup Django first!
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

try:
    print('Starting user creation...')
    User = get_user_model()
    
    users_to_create = [
        {
            'email': 'kelvin.reallife8@gmail.com',
            'role': 'admin',
            'is_superuser': True,
            'is_staff': True,
            'is_mfa_exempt': True,
            'is_verified': True
        },
        {
            'email': 'mystartupkenya@gmail.com',
            'role': 'director',
            'is_superuser': False,
            'is_staff': True,
            'is_mfa_exempt': True,
            'is_verified': True
        },
        {
            'email': 'kelvin202maina@gmail.com',
            'role': 'student',
            'is_superuser': False,
            'is_staff': False,
            'is_mfa_exempt': False,
            'is_verified': True
        }
    ]

    for u_data in users_to_create:
        email = u_data['email']
        user, created = User.objects.get_or_create(email=email)
        user.set_password(os.environ.get('USER_PASSWORD', ''))
        user.role = u_data['role']
        user.is_superuser = u_data['is_superuser']
        user.is_staff = u_data['is_staff']
        
        if hasattr(user, 'is_verified'):
            user.is_verified = u_data['is_verified']
        elif hasattr(user, 'email_verified'):
            user.email_verified = u_data['is_verified']
            
        if hasattr(user, 'is_mfa_exempt'):
            user.is_mfa_exempt = u_data['is_mfa_exempt']
        elif hasattr(user, 'mfa_exempt'):
            user.mfa_exempt = u_data['is_mfa_exempt']
            
        user.save()
        print(f"Successfully {'created' if created else 'updated'} {email} as {user.role}")
        
except Exception as e:
    import traceback
    print("Error creating users:")
    traceback.print_exc()
"""

def execute():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('69.30.235.220', username='administrator', password='Ongoza@#1', timeout=5)
        
        def run_sudo(cmd):
            stdin, stdout, stderr = c.exec_command(f'printf "Ongoza@#1\\n" | sudo -S -p "" {cmd}')
            return stdout.read().decode('utf-8').strip(), stderr.read().decode('utf-8').strip()
            
        print('--- Writing Django Script ---')
        write_cmd = f"cat << 'EOF' > /tmp/create_users2.py\n{script}\nEOF"
        c.exec_command(write_cmd)
        
        print('--- Executing inside Django Container ---')
        run_sudo('docker cp /tmp/create_users2.py hub_prod_django:/app/create_users2.py')
        out, err = run_sudo('docker exec hub_prod_django python /app/create_users2.py')
        print("OUTPUT:")
        print(out)
        print("ERROR:")
        print(err)
        
        print('\\n--- Fixing Missing Migrations Interactively ---')
        out, _ = run_sudo('docker exec hub_prod_django python manage.py makemigrations --no-input')
        print("MAKEMIGRATIONS:", out)
        out, _ = run_sudo('docker exec hub_prod_django python manage.py migrate --no-input')
        print("MIGRATE:", out)
        
    except Exception as e:
        print('Failed:', e)

if __name__ == '__main__':
    execute()
