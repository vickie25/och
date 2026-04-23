import os
import paramiko

def check_user_roles():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Use simple print and manual string concat to avoid quote issues
    py_cmd = (
        "from django.contrib.auth import get_user_model; "
        "User = get_user_model(); "
        "u = User.objects.get(id=13); "
        "print('Email: ' + u.email); "
        "print('Student: ' + str(getattr(u, 'is_student', 'N/A'))); "
        "print('Mentor: ' + str(getattr(u, 'is_mentor', 'N/A'))); "
        "print('Director: ' + str(getattr(u, 'is_director', 'N/A'))); "
    )
    
    cmd = f"docker exec hub_prod_django python manage.py shell -c \"{py_cmd}\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_user_roles()
