import os
import paramiko

def remove_users():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = """
from django.db import connection

emails_to_remove = ['kelvin202maina@gmail.com', 'featurekelvin@gmail.com', 'deleted_featurekelvin@gmail.com', 'featurekelvin_test@gmail.com']

with connection.cursor() as cursor:
    for email in emails_to_remove:
        # Get user ID first
        cursor.execute("SELECT id FROM users WHERE email = %s", [email])
        row = cursor.fetchone()
        if not row:
            print(f'SKIP: {email} not found')
            continue
        uid = row[0]
        
        # Delete related records first (cascade manually)
        tables = [
            ('user_roles', 'user_id'),
            ('mfa_methods', 'user_id'),
            ('mfa_codes', 'user_id'),
            ('user_sessions', 'user_id'),
            ('device_trusts', 'user_id'),
            ('audit_logs', 'user_id'),
            ('user_consents', 'user_id'),
        ]
        for table, col in tables:
            try:
                cursor.execute(f'DELETE FROM {table} WHERE {col} = %s', [uid])
            except Exception:
                pass  # Table might not exist
        
        # Now delete the user
        cursor.execute("DELETE FROM users WHERE id = %s", [uid])
        print(f'REMOVED: {email} (ID {uid})')

# Verify
cursor = connection.cursor()
cursor.execute("SELECT id, email FROM users ORDER BY id")
print('\\nREMAINING USERS:')
for row in cursor.fetchall():
    print(f'  ID {row[0]}: {row[1]}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    remove_users()
