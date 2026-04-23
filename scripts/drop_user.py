import os
import paramiko

def drop_user(email):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = f"""
from users.models import User
try:
    user = User.objects.get(email='{email}')
    user.delete()
    print(f'SUCCESS: User {email} deleted')
except User.DoesNotExist:
    print(f'INFO: User {email} not found')
except Exception as e:
    print(f'ERROR: {{str(e)}}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    drop_user('featurekelvin@gmail.com')
