import os
import paramiko

def remove_student_role():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Python script to remove student role
    script = """
from django.contrib.auth import get_user_model
from users.models import UserRole, Role
User = get_user_model()
email = 'kelvinmaina202@gmail.com'
try:
    u = User.objects.get(email=email)
    # Find student role
    try:
        student_role = Role.objects.get(name='student')
        user_roles = UserRole.objects.filter(user=u, role=student_role)
        count = user_roles.count()
        user_roles.delete()
        print(f'SUCCESS: Removed {count} student role(s) from {email}.')
    except Role.DoesNotExist:
        print('Role \"student\" does not exist.')
except User.DoesNotExist:
    print(f'User {email} not found.')
"""
    client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    
    # Verify remaining roles
    stdin, stdout, stderr = client.exec_command("docker exec hub_prod_django python manage.py shell -c \"from django.contrib.auth import get_user_model; from users.models import UserRole; u = get_user_model().objects.get(email='kelvinmaina202@gmail.com'); print('Remaining Roles: ' + str([r.role.name for r in u.user_roles.all()]))\"")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    remove_student_role()
