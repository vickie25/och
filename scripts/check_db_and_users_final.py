import os
import paramiko
import sys

def check_db_and_users():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [DJANGO DATABASE CONFIGURATION] ---")
        code = """
from django.conf import settings
from django.db import connection
print(f"Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"Name: {settings.DATABASES['default']['NAME']}")
print(f"User: {settings.DATABASES['default']['USER']}")
print(f"Host: {settings.DATABASES['default']['HOST']}")

with connection.cursor() as cursor:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('users', 'django_migrations')")
    print(f"Existing project tables: {[r[0] for r in cursor.fetchall()]}")
    
    cursor.execute("SELECT name FROM django_migrations WHERE app='users'")
    print(f"Users migrations in DB: {[r[0] for r in cursor.fetchall()]}")
"""
        command = f"sudo docker exec hub_prod_django python manage.py shell -c \"{code}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_db_and_users()
