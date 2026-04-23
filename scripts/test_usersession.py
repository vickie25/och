import os
import paramiko
import sys

def test_user_session():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [TESTING USERSESSION CREATION] ---")
        # Try to import and create a dummy UserSession
        code = """
try:
    from django.contrib.auth import get_user_model
    from users.auth_models import UserSession
    from django.utils import timezone
    User = get_user_model()
    u = User.objects.first()
    if u:
        print(f"User: {u.email}")
        # Just count sessions to see if table exists
        count = UserSession.objects.count()
        print(f"Session count: {count}")
    else:
        print("No users found")
except Exception as e:
    import traceback
    print(f"FAILED: {str(e)}")
    print(traceback.format_exc())
"""
        command = f"sudo docker exec hub_prod_django python manage.py shell -c '{code}'"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_user_session()
