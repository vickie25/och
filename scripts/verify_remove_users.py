import os
import paramiko

def verify_and_remove():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = """
from django.db import connection

emails = ['kelvin202maina@gmail.com', 'featurekelvin@gmail.com', 'deleted_featurekelvin@gmail.com', 'featurekelvin_test@gmail.com']

with connection.cursor() as c:
    for email in emails:
        c.execute("SELECT id FROM users WHERE email = %s", [email])
        row = c.fetchone()
        if not row:
            print(f'ALREADY GONE: {email}')
            continue
        uid = row[0]
        print(f'FOUND: {email} (ID {uid}) - removing...')
        
        # Clean related tables
        for tbl in ['user_roles', 'mfa_methods', 'mfa_codes', 'user_sessions', 'device_trusts', 'audit_logs', 'user_consents']:
            try:
                c.execute(f'DELETE FROM {tbl} WHERE user_id = %s', [uid])
            except Exception as e:
                print(f'  skip {tbl}: {e}')
        
        # Delete user
        try:
            c.execute('DELETE FROM users WHERE id = %s', [uid])
            print(f'  DELETED OK')
        except Exception as e:
            print(f'  DELETE FAILED: {e}')

    # Show remaining
    c.execute("SELECT id, email, account_status FROM users ORDER BY id")
    print(f'\\nREMAINING USERS:')
    for r in c.fetchall():
        print(f'  ID {r[0]}: {r[1]} ({r[2]})')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    out = stdout.read().decode()
    err = stderr.read().decode()
    print(out)
    if err.strip():
        print(f"STDERR: {err}")
    
    client.close()

if __name__ == "__main__":
    verify_and_remove()
