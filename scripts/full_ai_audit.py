import paramiko
import sys

def full_ai_audit():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))

    def run(cmd, label):
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        print(f"\n{'='*70}")
        print(f"  {label}")
        print(f"{'='*70}")
        if out.strip():
            print(out.strip())
        if err.strip() and 'WARNING' not in err:
            print(f"STDERR: {err.strip()[:500]}")
        return out

    # =============================================
    # 1. AI-RELATED ENVIRONMENT VARIABLES
    # =============================================
    run('docker exec hub_prod_django env | grep -iE "OPENAI|GPT|GROQ|LLAMA|AI_|PROFIL|REDIS|FASTAPI"',
        '1. AI ENVIRONMENT VARIABLES IN DJANGO')

    run('docker exec hub_prod_django env | grep -iE "CHAT_GPT|OPENAI_API"',
        '1b. OPENAI/GPT API KEYS')

    # =============================================
    # 2. REDIS CONNECTIVITY TEST
    # =============================================
    run('docker exec hub_prod_redis redis-cli PING', '2. REDIS PING TEST')
    run('docker exec hub_prod_redis redis-cli INFO memory | head -5', '2b. REDIS MEMORY')

    # =============================================
    # 3. AI PROFILER - Test session start endpoint
    # =============================================
    profiler_test = """
import urllib.request, json

# Test the profiler endpoint
url = 'http://localhost:8000/api/profiling/session/start'
req = urllib.request.Request(url, data=b'{}', headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as resp:
        print(f'STATUS: {resp.status}')
        print(f'BODY: {resp.read().decode()[:500]}')
except urllib.error.HTTPError as e:
    print(f'STATUS: {e.code}')
    body = e.read().decode()[:500]
    print(f'BODY: {body}')
except Exception as e:
    print(f'ERROR: {e}')
"""
    run(f"docker exec -i hub_prod_django python << 'EOF'\n{profiler_test}\nEOF",
        '3. AI PROFILER SESSION START TEST')

    # =============================================
    # 4. AI COACH - Test chat endpoint
    # =============================================
    coach_test = """
import urllib.request, json

url = 'http://localhost:8000/api/v1/coaching/ai-coach/chat'
data = json.dumps({'message': 'hello', 'session_id': 'test'}).encode()
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as resp:
        print(f'STATUS: {resp.status}')
        print(f'BODY: {resp.read().decode()[:500]}')
except urllib.error.HTTPError as e:
    print(f'STATUS: {e.code}')
    body = e.read().decode()[:500]
    print(f'BODY: {body}')
except Exception as e:
    print(f'ERROR: {e}')
"""
    run(f"docker exec -i hub_prod_django python << 'EOF'\n{coach_test}\nEOF",
        '4. AI COACH CHAT TEST')

    # =============================================
    # 5. TEST OPENAI API KEY VALIDITY
    # =============================================
    openai_test = """
import os, json, urllib.request

key = os.environ.get('OPENAI_API_KEY', '') or os.environ.get('CHAT_GPT_API_KEY', '')
if not key:
    print('NO OPENAI KEY FOUND')
else:
    print(f'KEY PREFIX: {key[:20]}...')
    req = urllib.request.Request(
        'https://api.openai.com/v1/models',
        headers={'Authorization': f'Bearer {key}'}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            models = [m['id'] for m in data.get('data', []) if 'gpt' in m['id'].lower()][:5]
            print(f'OPENAI KEY VALID: True')
            print(f'AVAILABLE GPT MODELS: {models}')
    except urllib.error.HTTPError as e:
        print(f'OPENAI KEY VALID: False (HTTP {e.code})')
        print(f'DETAIL: {e.read().decode()[:300]}')
    except Exception as e:
        print(f'OPENAI KEY TEST ERROR: {e}')
"""
    run(f"docker exec -i hub_prod_django python << 'EOF'\n{openai_test}\nEOF",
        '5. OPENAI API KEY VALIDATION')

    # =============================================
    # 6. TEST GROQ API KEY (LLAMA FALLBACK)
    # =============================================
    groq_test = """
import os, json, urllib.request

key = os.environ.get('GROQ_API_KEY', '')
if not key:
    print('NO GROQ KEY FOUND')
else:
    print(f'KEY PREFIX: {key[:20]}...')
    req = urllib.request.Request(
        'https://api.groq.com/openai/v1/models',
        headers={'Authorization': f'Bearer {key}'}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            models = [m['id'] for m in data.get('data', [])][:5]
            print(f'GROQ KEY VALID: True')
            print(f'AVAILABLE MODELS: {models}')
    except urllib.error.HTTPError as e:
        print(f'GROQ KEY VALID: False (HTTP {e.code})')
        print(f'DETAIL: {e.read().decode()[:300]}')
    except Exception as e:
        print(f'GROQ KEY TEST ERROR: {e}')
"""
    run(f"docker exec -i hub_prod_django python << 'EOF'\n{groq_test}\nEOF",
        '6. GROQ/LLAMA FALLBACK KEY VALIDATION')

    # =============================================
    # 7. LIST ALL AI-RELATED URL ENDPOINTS
    # =============================================
    urls_check = """
from django.urls import get_resolver
resolver = get_resolver()

ai_patterns = []
def walk(patterns, prefix=''):
    for p in patterns:
        full = prefix + str(getattr(p.pattern, '_route', '') or str(p.pattern))
        if hasattr(p, 'url_patterns'):
            walk(p.url_patterns, full)
        else:
            if any(kw in full.lower() for kw in ['profil', 'coach', 'ai', 'recipe', 'chat', 'groq', 'llama']):
                ai_patterns.append(full)

walk(resolver.url_patterns)
for p in sorted(set(ai_patterns)):
    print(f'  {p}')
if not ai_patterns:
    print('  NO AI ENDPOINTS FOUND IN URL PATTERNS')
"""
    run(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{urls_check}\nEOF",
        '7. ALL AI-RELATED URL ENDPOINTS')

    # =============================================
    # 8. CHECK FASTAPI CONTAINER (profiler often runs here)
    # =============================================
    run('docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -iE "fast|profil|ai|coach"',
        '8. FASTAPI / AI CONTAINERS STATUS')

    run('docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"',
        '8b. ALL RUNNING CONTAINERS')

    # =============================================
    # 9. CHECK DJANGO LOGS FOR AI ERRORS
    # =============================================
    run('docker logs --tail 50 hub_prod_django 2>&1 | grep -iE "profil|coach|openai|groq|500|error|traceback"',
        '9. RECENT AI-RELATED ERRORS IN DJANGO LOGS')

    # =============================================
    # 10. CHECK NGINX PROXY ROUTES FOR /api/profiling
    # =============================================
    run('docker exec hub_prod_nginx cat /etc/nginx/conf.d/default.conf | grep -A3 -iE "profil|fastapi|8001"',
        '10. NGINX ROUTES FOR PROFILER/FASTAPI')

    client.close()
    print(f"\n{'='*70}")
    print(f"  FULL AI AUDIT COMPLETE")
    print(f"{'='*70}")

if __name__ == "__main__":
    full_ai_audit()
