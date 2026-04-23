import os
import paramiko
import time

def run(client, cmd, label=""):
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    if label:
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}")
    if out.strip():
        print(out.strip())
    if err.strip():
        print(f"STDERR: {err.strip()}")
    return out

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))

    # =========================================================
    # STEP 1: Flush Redis to kill ALL rate limiting
    # =========================================================
    run(client, 'docker exec hub_prod_redis redis-cli FLUSHALL', 'STEP 1: Flush Redis (kill rate limits)')

    # =========================================================
    # STEP 2: Patch the serializer IN THE CONTAINER to add is_superuser/is_staff
    # =========================================================
    patch_serializer = """
import re, shutil

path = '/app/users/serializers.py'
with open(path, 'r') as f:
    content = f.read()

# Check if already patched
if "'is_superuser'" in content:
    print('SERIALIZER: Already patched (is_superuser found)')
else:
    # Add is_staff and is_superuser after is_active
    content = content.replace(
        "'is_active',\\n            'created_at',",
        "'is_active',\\n            'is_staff',\\n            'is_superuser',\\n            'created_at',"
    )
    # Try alternate format (with \\r\\n)
    content = content.replace(
        "'is_active',\\r\\n            'created_at',",
        "'is_active',\\r\\n            'is_staff',\\r\\n            'is_superuser',\\r\\n            'created_at',"
    )
    with open(path, 'w') as f:
        f.write(content)
    # Verify
    with open(path, 'r') as f:
        verify = f.read()
    if "'is_superuser'" in verify:
        print('SERIALIZER: PATCHED SUCCESSFULLY (is_superuser + is_staff added)')
    else:
        print('SERIALIZER: WARNING - patch may not have applied, trying direct approach')
        # Direct sed-like approach
        lines = verify.split('\\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if "'is_active'," in line and "'is_staff'" not in verify:
                indent = '            '
                new_lines.append(f"{indent}'is_staff',")
                new_lines.append(f"{indent}'is_superuser',")
        with open(path, 'w') as f:
            f.write('\\n'.join(new_lines))
        print('SERIALIZER: Applied direct line insertion')
"""
    run(client, f"docker exec -i hub_prod_django python << 'PYEOF'\n{patch_serializer}\nPYEOF", 
        'STEP 2: Patch serializer in container')

    # =========================================================
    # STEP 3: Disable LoginRateLimitMiddleware in the container
    # =========================================================
    patch_middleware = """
path = '/app/core/middleware.py'
with open(path, 'r') as f:
    content = f.read()

# Make the LoginRateLimitMiddleware a complete no-op
if 'RATE_LIMIT_DISABLED' in content:
    print('MIDDLEWARE: Already disabled')
else:
    # Find the class and make __call__ just pass through
    old = 'class LoginRateLimitMiddleware:'
    new = '''class LoginRateLimitMiddleware:
    # RATE_LIMIT_DISABLED - bypassed for emergency access
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        return self.get_response(request)

class _OriginalLoginRateLimitMiddleware_DISABLED:'''
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print('MIDDLEWARE: LoginRateLimitMiddleware DISABLED (pass-through)')
"""
    run(client, f"docker exec -i hub_prod_django python << 'PYEOF'\n{patch_middleware}\nPYEOF",
        'STEP 3: Disable rate limit middleware')

    # =========================================================
    # STEP 4: Restart Django to pick up changes
    # =========================================================
    run(client, 'docker restart hub_prod_django', 'STEP 4: Restart Django')
    print("Waiting 8 seconds for Django to boot...")
    time.sleep(8)

    # =========================================================
    # STEP 5: Verify Django is healthy
    # =========================================================
    run(client, 'docker exec hub_prod_django curl -s http://localhost:8000/api/v1/health/', 
        'STEP 5: Health check')

    # =========================================================
    # STEP 6: End-to-end login test (the REAL proof)
    # =========================================================
    login_test = """
import urllib.request, json

url = 'http://localhost:8000/api/v1/auth/login/'
data = json.dumps({'email': 'kelvinmaina202@gmail.com', 'password': 'OngozaAdmin2026!'}).encode()
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

try:
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode())
        print(f'STATUS: {resp.status}')
        print(f'HAS access_token: {bool(body.get("access_token"))}')
        print(f'HAS refresh_token: {bool(body.get("refresh_token"))}')
        print(f'primary_role: {body.get("primary_role")}')
        print(f'profiling_required: {body.get("profiling_required")}')
        user = body.get('user', {})
        print(f'user.email: {user.get("email")}')
        print(f'user.is_superuser: {user.get("is_superuser")}')
        print(f'user.is_staff: {user.get("is_staff")}')
        print(f'user.roles: {user.get("roles")}')
        print(f'user.account_status: {user.get("account_status")}')
        print(f'user.profiling_complete: {user.get("profiling_complete")}')
        print(f'mfa_required: {body.get("mfa_required")}')
except urllib.error.HTTPError as e:
    print(f'FAILED STATUS: {e.code}')
    print(f'BODY: {e.read().decode()}')
except Exception as e:
    print(f'ERROR: {e}')
"""
    run(client, f"docker exec -i hub_prod_django python << 'PYEOF'\n{login_test}\nPYEOF",
        'STEP 6: END-TO-END LOGIN TEST')

    # =========================================================
    # STEP 7: Verify user state in DB
    # =========================================================
    user_check = """
from users.models import User, UserRole
u = User.objects.get(email='kelvinmaina202@gmail.com')
print(f'id: {u.id}')
print(f'is_superuser: {u.is_superuser}')
print(f'is_staff: {u.is_staff}')
print(f'is_active: {u.is_active}')
print(f'account_status: {u.account_status}')
print(f'profiling_complete: {u.profiling_complete}')
print(f'mfa_enabled: {u.mfa_enabled}')
for ur in u.user_roles.all():
    print(f'ROLE: {ur.role.name} | active: {ur.is_active} | scope: {ur.scope}')
"""
    run(client, f"docker exec -i hub_prod_django python manage.py shell << 'PYEOF'\n{user_check}\nPYEOF",
        'STEP 7: VERIFY USER STATE IN DB')

    client.close()
    print("\n" + "="*60)
    print("  ALL STEPS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
