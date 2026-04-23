import paramiko
import sys

def verify_provisioning():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    django_script = """
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.contrib.auth import get_user_model
from users.models import UserRole

User = get_user_model()
u = User.objects.filter(email='featurekelvin@gmail.com').first()

if u:
    print("=== VERIFICATION RESULTS ===")
    print(f"Name: {u.first_name} {u.last_name}")
    print(f"Is Superuser: {u.is_superuser}")
    print(f"Is Staff: {u.is_staff}")
    print(f"Email Verified: {u.email_verified}")
    print(f"Account Status: {u.account_status}")
    print(f"MFA Enabled: {u.mfa_enabled}")
    
    roles = list(u.user_roles.values_list('role__name', flat=True))
    print(f"Roles: {roles}")
else:
    print("ERROR: User not found!")
"""

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # Save script to temporal location dynamically
        client.exec_command(f"cat << 'EOF' > /tmp/verify_kelvin.py\n{django_script}\nEOF")
        
        # Execute in Django container
        command = "sudo docker exec -i hub_prod_django python3 /tmp/verify_kelvin.py"
        # Since /tmp/verify_kelvin.py is on the host, we actually need to pipe it or copy it into the container.
        
        command = "sudo docker exec -i hub_prod_django python3 -"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        
        stdin.write(django_script)
        stdin.close()
        
        print("\n--- [PROVISIONING VERIFICATION] ---")
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    verify_provisioning()
