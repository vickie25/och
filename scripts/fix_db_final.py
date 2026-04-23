import os
import paramiko

def fix_everything():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = """
from django.db import connection
from users.models import User, UserRole, Role

# =============================================
# STEP 1: Make kelvin202maina super admin
# =============================================
u = User.objects.get(email='kelvin202maina@gmail.com')
u.set_password('OngozaAdmin2026!')
u.is_superuser = True
u.is_staff = True
u.account_status = 'active'
u.is_active = True
u.profiling_complete = True
u.mfa_enabled = False
u.save()

# Remove any student role
u.user_roles.filter(role__name='student').delete()

# Add admin role
admin_role, _ = Role.objects.get_or_create(name='admin', defaults={'display_name': 'Administrator'})
UserRole.objects.get_or_create(user=u, role=admin_role, defaults={'scope': 'global', 'is_active': True})

print(f'DONE: kelvin202maina@gmail.com -> superadmin (ID {u.id})')

# =============================================
# STEP 2: Clean junk accounts
# =============================================
junk_emails = [
    'featurekelvin@gmail.com',
    'deleted_featurekelvin@gmail.com',
    'featurekelvin_test@gmail.com',
    'profiler-smoke@example.com',
    'pay_smoke_dd6f0727e7@example.com',
    'pay_smoke_adfcb5fade@example.com',
]

with connection.cursor() as c:
    for email in junk_emails:
        c.execute("SELECT id FROM users WHERE email = %s", [email])
        row = c.fetchone()
        if not row:
            print(f'SKIP: {email} not found')
            continue
        uid = row[0]
        
        # Nuke ALL related records across every known table
        related_tables = [
            'user_roles', 'mfa_methods', 'mfa_codes', 'user_sessions',
            'audit_logs', 'community_user_stats', 'ai_coach_sessions',
            'ai_coach_messages', 'student_progress', 'user_track_enrollments',
            'student_certifications', 'payment_transactions', 'user_entitlements',
        ]
        for tbl in related_tables:
            try:
                c.execute(f'DELETE FROM {tbl} WHERE user_id = %s', [uid])
            except Exception:
                pass
        
        # Delete the user
        try:
            c.execute('DELETE FROM users WHERE id = %s', [uid])
            print(f'REMOVED: {email} (ID {uid})')
        except Exception as e:
            # If still blocked, find what table is blocking
            err = str(e)
            if 'foreign key' in err:
                # Extract table name from error
                import re
                match = re.search(r'on table "([^"]+)"', err)
                blocking_table = match.group(1) if match else 'unknown'
                try:
                    c.execute(f'DELETE FROM {blocking_table} WHERE user_id = %s', [uid])
                    c.execute('DELETE FROM users WHERE id = %s', [uid])
                    print(f'REMOVED: {email} (ID {uid}) [cleared {blocking_table}]')
                except Exception as e2:
                    print(f'FAILED: {email} - {e2}')
            else:
                print(f'FAILED: {email} - {e}')

# =============================================
# STEP 3: Final verification
# =============================================
print(f'\\n{"="*70}')
print(f'FINAL DATABASE STATE:')
print(f'{"="*70}')
for u2 in User.objects.all().order_by('id'):
    roles = ', '.join([ur.role.name for ur in u2.user_roles.filter(is_active=True)]) or 'NONE'
    su = 'SUPERADMIN' if u2.is_superuser else ''
    print(f'  ID {u2.id}: {u2.email} | {u2.account_status} | {roles} {su}')
print(f'TOTAL: {User.objects.count()} users')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err.strip():
        print(f"STDERR: {err}")
    
    client.close()

if __name__ == "__main__":
    fix_everything()
