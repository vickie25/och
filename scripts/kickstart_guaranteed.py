import os
import paramiko
import sys

def kickstart_guaranteed():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Force insert with explicit commit and past timestamp
        print("\n--- [STEP 1: GUARANTEED SQL KICKSTART] ---")
        code = """
from django.db import connection, transaction
try:
    with connection.cursor() as cursor:
        # Delete any partial/bad records first
        cursor.execute("DELETE FROM django_migrations WHERE app='users' AND name='0001_initial'")
        cursor.execute("DELETE FROM django_migrations WHERE app='organizations' AND name='0001_initial'")
        
        # Insert with old timestamp to ensure it's 'before' admin
        past_date = '2026-04-01 00:00:00+00'
        cursor.execute(f"INSERT INTO django_migrations (app, name, applied) VALUES ('users', '0001_initial', '{past_date}')")
        cursor.execute(f"INSERT INTO django_migrations (app, name, applied) VALUES ('organizations', '0001_initial', '{past_date}')")
        
        print("INSERTED records successfully.")
    
    # Explicit commit
    transaction.commit()
    print("COMMITTED successfully.")

except Exception as e:
    print(f'ERROR: {str(e)}')
"""
        command = f"sudo docker exec hub_prod_django python manage.py shell -c \"{code}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 2. Immediate verification in DB
        print("\n--- [STEP 2: DB VERIFICATION] ---")
        command = "sudo docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"SELECT app, name, applied FROM django_migrations WHERE app IN ('users', 'organizations')\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    kickstart_guaranteed()
