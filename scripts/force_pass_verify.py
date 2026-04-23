import os
import paramiko

def force_password_reset_and_verify():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = """
from users.models import User
from django.db import transaction

email = 'kelvinmaina202@gmail.com'
password = os.environ.get('USER_PASSWORD', '')

try:
    with transaction.atomic():
        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()
        
        # Verify immediately
        is_ok = user.check_password(password)
        print(f'PASSWORD_SET: True')
        print(f'VERIFICATION_SUCCESS: {is_ok}')
        print(f'USER_ID: {user.id}')
except Exception as e:
    print(f'ERROR: {str(e)}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    force_password_reset_and_verify()
