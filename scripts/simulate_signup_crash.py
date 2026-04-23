import os
import paramiko

def simulate_signup_crash():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = """
from users.models import User
from django.db import transaction

email = 'featurekelvin_test@gmail.com'
password = 'TestPassword123!'

try:
    with transaction.atomic():
        user = User.objects.create_user(
            email=email,
            username=email,
            password=password,
            first_name='Test',
            last_name='User'
        )
        print(f'SUCCESS: User created with ID {user.id}')
except Exception as e:
    import traceback
    print(f'CRASH_TRACEBACK:\\n{traceback.format_exc()}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    simulate_signup_crash()
