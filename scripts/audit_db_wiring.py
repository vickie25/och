import os
import paramiko

def check_db_wiring():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Check DB_HOST and also the number of users to confirm which DB we are in
    script = """
from django.conf import settings
from django.contrib.auth import get_user_model
User = get_user_model()
db_host = settings.DATABASES['default']['HOST']
user_count = User.objects.count()
print(f'ACTUAL_DB_HOST: {db_host}')
print(f'USER_COUNT: {user_count}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_db_wiring()
