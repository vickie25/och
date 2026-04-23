import os
import paramiko

def strip_student_roles():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = """
from users.models import User, UserRole

email = 'kelvinmaina202@gmail.com'
user = User.objects.get(email=email)

# Find any student or mentee roles
student_roles = user.user_roles.filter(role__name__in=['student', 'mentee'])
count = student_roles.count()

if count > 0:
    student_roles.delete()
    print(f'CLEANUP: Removed {count} student/mentee roles from {email}')
else:
    print(f'CLEANUP: No student roles found for {email}')

# Ensure profiling_complete is True just in case
if not user.profiling_complete:
    user.profiling_complete = True
    user.save(update_fields=['profiling_complete'])
    print(f'CLEANUP: Force-marked profiling as COMPLETE for {email}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    strip_student_roles()
