import paramiko
import sys

def audit_roles_and_user():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    target_email = "featurekelvin@gmail.com"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [PRODUCTION AUTH AUDIT] ---")
        
        # Script to run in Django
        django_script = f"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from users.models import User, Role, UserRole

print("\\n[AVAILABLE ROLES]")
roles = list(Role.objects.values_list('name', flat=True))
print(roles)

print(f"\\n[CHECKING USER: {target_email}]")
u = User.objects.filter(email='{target_email}').first()
if u:
    print(f"Found User: {{u.email}} (ID={{u.id}})")
    print(f"Flags: is_staff={{u.is_staff}}, is_superuser={{u.is_superuser}}, verified={{u.email_verified}}")
    print(f"Roles: {{list(u.user_roles.values_list('role__name', flat=True))}}")
else:
    print("User not found.")
"""
        # Save logic to host
        client.exec_command(f"cat << 'EOF' > /tmp/audit_auth.py\n{django_script}\nEOF")
        
        # Run inside container
        command = "sudo docker exec -i hub_prod_django python3 -"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        
        stdin.write(django_script)
        stdin.close()
        
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    audit_roles_and_user()
