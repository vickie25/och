import os
import paramiko

def rename_user(old_email, new_email):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = f"""
from users.models import User
try:
    user = User.objects.get(email='{old_email}')
    user.email = '{new_email}'
    user.username = '{new_email}'
    user.save()
    print(f'SUCCESS: User {old_email} renamed to {new_email}')
except User.DoesNotExist:
    print(f'INFO: User {old_email} not found')
except Exception as e:
    print(f'ERROR: {{str(e)}}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    rename_user('featurekelvin@gmail.com', 'deleted_featurekelvin@gmail.com')
