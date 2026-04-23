import os
import paramiko
import sys

def check_db_summary():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [DB CONFIG] ---")
        command = "sudo docker exec hub_prod_django python manage.py shell -c \"from django.conf import settings; print(settings.DATABASES['default']['NAME'])\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        print("\n--- [USERS MIGRATIONS COUNT] ---")
        command = "sudo docker exec hub_prod_django python manage.py shell -c \"from django.db import connection; cursor=connection.cursor(); cursor.execute('SELECT COUNT(*) FROM django_migrations WHERE app=\\'users\\''); print(cursor.fetchone()[0])\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_db_summary()
