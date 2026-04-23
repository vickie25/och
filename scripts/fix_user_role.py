import paramiko

def fix_user_role():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    django_script = """
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from users.models import User, UserRole, Role

email = 'featurekelvin@gmail.com'

try:
    u = User.objects.get(email=email)
    roles = UserRole.objects.filter(user=u)
    print(f"Found {roles.count()} roles for user {email}")
    
    for r in roles:
        role_name = getattr(r.role, 'name', str(r.role))
        print(f"Role: {role_name}, is_active before: {r.is_active}")
        r.is_active = True
        r.save()
    
    def dictfetchall(cursor):
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users_userrole WHERE user_id = %s", [u.id])
        rows = dictfetchall(cursor)
        for row in rows:
            print(f"Database row: {row}")

    from users.serializers import UserSerializer
    d = UserSerializer(u).data
    print(f"\\nSerializer roles: {d.get('roles')}")
    print(f"Serializer primary_role: {d.get('primary_role')}")
    print("FIX APPLIED SUCCESSFULLY.")
    
except Exception as e:
    import traceback
    traceback.print_exc()
"""

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [FIXING USER ROLE is_active FLAG] ---")
        
        command = "sudo docker exec -i hub_prod_django python3 manage.py shell"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        
        stdin.write(django_script)
        stdin.close()
        
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    fix_user_role()
