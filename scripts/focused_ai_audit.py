import paramiko

def focused_audit():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))

    def run(cmd, label):
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='ignore')
        print(f"\n{'='*60}\n  {label}\n{'='*60}")
        if out.strip(): print(out.strip())
        return out

    # 1. OpenAI key test
    script1 = """
import os, json, urllib.request
key = os.environ.get('OPENAI_API_KEY', '') or os.environ.get('CHAT_GPT_API_KEY', '')
print(f'KEY EXISTS: {bool(key)}')
print(f'KEY PREFIX: {key[:25]}...' if key else 'NO KEY')
if key:
    req = urllib.request.Request('https://api.openai.com/v1/models', headers={'Authorization': f'Bearer {key}'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            models = [m['id'] for m in data.get('data', []) if 'gpt' in m['id'].lower()][:5]
            print(f'VALID: True')
            print(f'GPT MODELS: {models}')
    except urllib.error.HTTPError as e:
        print(f'VALID: False (HTTP {e.code})')
        print(f'DETAIL: {e.read().decode()[:300]}')
    except Exception as e:
        print(f'ERROR: {e}')
"""
    run(f"docker exec -i hub_prod_django python << 'EOF'\n{script1}\nEOF", 'OPENAI KEY TEST')

    # 2. Groq key test
    script2 = """
import os
key = os.environ.get('GROQ_API_KEY', '')
print(f'GROQ_API_KEY EXISTS: {bool(key)}')
if key:
    print(f'KEY PREFIX: {key[:20]}...')
else:
    print('NO GROQ KEY - LLAMA FALLBACK WILL NOT WORK')
"""
    run(f"docker exec -i hub_prod_django python << 'EOF'\n{script2}\nEOF", 'GROQ KEY CHECK')

    # 3. FastAPI health + env
    run('docker exec hub_prod_fastapi env | grep -iE "OPENAI|GROQ|REDIS|API_KEY|MODEL"', 'FASTAPI ENV VARS')
    
    script3 = """
import urllib.request
try:
    with urllib.request.urlopen('http://localhost:8001/health') as r:
        print(f'FASTAPI HEALTH: {r.status} - {r.read().decode()[:200]}')
except Exception as e:
    print(f'FASTAPI HEALTH ERROR: {e}')
"""
    run(f"docker exec -i hub_prod_fastapi python << 'EOF'\n{script3}\nEOF", 'FASTAPI HEALTH TEST')

    # 4. Check the profiler Next.js route
    run('docker exec hub_prod_nextjs ls -la /app/app/api/profiling/ 2>/dev/null || echo "NO PROFILING ROUTE DIR"', 
        'NEXTJS PROFILING ROUTE FILES')
    run('docker exec hub_prod_nextjs find /app/app/api/profiling -name "route.*" 2>/dev/null || echo "NO ROUTES FOUND"',
        'NEXTJS PROFILING ROUTE PATHS')

    # 5. AI Coach view source check
    script5 = """
import inspect
try:
    from coaching.views import AIChatView
    print('AI COACH VIEW: Found')
    print(f'MODULE: {inspect.getfile(AIChatView)}')
except ImportError as e:
    print(f'AI COACH VIEW: Not found - {e}')
try:
    from coaching.ai_coach_service import AICoachService
    print('AI COACH SERVICE: Found')
    print(f'MODULE: {inspect.getfile(AICoachService)}')
except ImportError as e:
    print(f'AI COACH SERVICE: Not found - {e}')
"""
    run(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script5}\nEOF", 'AI COACH CODE CHECK')

    client.close()

if __name__ == "__main__":
    focused_audit()
