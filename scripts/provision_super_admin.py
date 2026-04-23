import paramiko
import sys

def provision_super_admin():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    django_script = """
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Role, UserRole

User = get_user_model()
email = 'featurekelvin@gmail.com'

# 1. Provide the user account
user, created = User.objects.get_or_create(email=email, defaults={'username': email})

print(f"User {email} {'created' if created else 'found'}.")

# 2. Set Super Admin attributes and MFA Exemption
user.first_name = "Kelvin"
user.last_name = "Maina"
user.is_staff = True
user.is_superuser = True
user.email_verified = True
user.account_status = "active"
user.mfa_enabled = False
user.set_password(os.environ.get('USER_PASSWORD', ''))
user.save()

print("User attributes (names, superuser status, mfa exemption) updated successfully.")

# 3. Ensure 'admin' role in UserRole
role, _ = Role.objects.get_or_create(name='admin', defaults={'display_name': 'Administrator'})

user_role, role_created = UserRole.objects.get_or_create(
    user=user, 
    role=role, 
    scope='global',
    defaults={'is_active': True}
)

print(f"Role 'admin' (global scope) {'assigned' if role_created else 'already assigned'} to user.")
print("PROVISIONING COMPLETE. User 'featurekelvin@gmail.com' is now a Super Admin, ready to access the dashboard.")
"""

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [PROVISIONING KELVIN MAINA SUPER ADMIN] ---")
        
        # Save script to temporal location dynamically
        client.exec_command(f"cat << 'EOF' > /tmp/provision_kelvin.py\n{django_script}\nEOF")
        
        # Execute in Django container
        command = "sudo docker exec -i hub_prod_django python3 -"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        
        stdin.write(django_script)
        stdin.close()
        
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    provision_super_admin()
