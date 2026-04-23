import os
import paramiko

def final_cleanup():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = """
from django.db import connection

junk = [
    ('featurekelvin@gmail.com', 14),
    ('deleted_featurekelvin@gmail.com', 9),
    ('profiler-smoke@example.com', 10),
]

with connection.cursor() as c:
    for email, uid in junk:
        # Find ALL tables that reference users.id
        c.execute(\"\"\"
            SELECT tc.table_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = 'users' AND ccu.column_name = 'id'
        \"\"\")
        fk_tables = c.fetchall()
        
        for table_name, col_name in fk_tables:
            try:
                c.execute(f'DELETE FROM "{table_name}" WHERE "{col_name}" = %s', [uid])
            except Exception:
                pass
        
        # Now delete the user (using id, not user_id)
        try:
            c.execute('DELETE FROM users WHERE id = %s', [uid])
            print(f'REMOVED: {email} (ID {uid})')
        except Exception as e:
            print(f'STILL BLOCKED: {email} - {e}')

    # Final count
    c.execute("SELECT id, email FROM users ORDER BY id")
    print(f'\\nCLEAN DATABASE:')
    for r in c.fetchall():
        print(f'  ID {r[0]}: {r[1]}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    final_cleanup()
