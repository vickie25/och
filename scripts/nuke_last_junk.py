import os
import paramiko

def nuke_last_junk():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = """
from django.db import connection
uid = 9
with connection.cursor() as c:
    # Manually clear ai_coach_sessions and any messages
    for tbl in ['ai_coach_messages', 'ai_coach_sessions', 'community_user_stats']:
        try:
            c.execute(f'DELETE FROM {tbl} WHERE user_id = %s', [uid])
            print(f'  Cleared {tbl}')
        except Exception as e:
            print(f'  {tbl}: {e}')
    
    # Also try session_id references
    try:
        c.execute('SELECT id FROM ai_coach_sessions WHERE user_id = %s', [uid])
        sessions = [r[0] for r in c.fetchall()]
        for sid in sessions:
            c.execute('DELETE FROM ai_coach_messages WHERE session_id = %s', [sid])
        c.execute('DELETE FROM ai_coach_sessions WHERE user_id = %s', [uid])
        print('  Cleared ai_coach_sessions (with messages)')
    except Exception as e:
        print(f'  ai_coach deep clean: {e}')
    
    try:
        c.execute('DELETE FROM users WHERE id = %s', [uid])
        print(f'REMOVED: ID {uid}')
    except Exception as e:
        print(f'STILL BLOCKED: {e}')
    
    c.execute("SELECT id, email FROM users ORDER BY id")
    print(f'\\nFINAL CLEAN DATABASE:')
    for r in c.fetchall():
        print(f'  ID {r[0]}: {r[1]}')
    print(f'TOTAL: {len(c.fetchall()) if False else "see above"}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    client.close()

if __name__ == "__main__":
    nuke_last_junk()
