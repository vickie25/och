import paramiko

def deep_ai_audit():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))

    def run(cmd, label):
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='ignore')
        print(f"\n{'='*60}\n  {label}\n{'='*60}")
        if out.strip(): print(out.strip())
        return out

    # FastAPI full env
    run('docker exec hub_prod_fastapi env | sort', 'FASTAPI FULL ENV')

    # FastAPI routes
    script1 = """
import urllib.request, json
try:
    with urllib.request.urlopen('http://localhost:8001/openapi.json') as r:
        data = json.loads(r.read().decode())
        paths = list(data.get('paths', {}).keys())
        print(f'TOTAL ENDPOINTS: {len(paths)}')
        for p in sorted(paths):
            print(f'  {p}')
except Exception as e:
    print(f'ERROR: {e}')
"""
    run(f"docker exec -i hub_prod_fastapi python << 'EOF'\n{script1}\nEOF", 'FASTAPI API ENDPOINTS')

    # NextJS env for FastAPI URL
    run('docker exec hub_prod_nextjs env | grep -iE "FAST|PROFIL|AI"', 'NEXTJS FASTAPI ENV VARS')

    # AI Coach - find the actual view
    script2 = """
import os
# Search for ai-coach or ai_coach
for root, dirs, files in os.walk('/app/coaching'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fh:
                content = fh.read()
                if 'ai-coach' in content or 'ai_coach' in content or 'AIChatView' in content or 'AICoach' in content:
                    print(f'FOUND: {path}')
                    # Find the class or function
                    for i, line in enumerate(content.split('\\n')):
                        if any(kw in line for kw in ['class ', 'def ', 'AICoach', 'ai_coach', 'generate_response']):
                            print(f'  L{i+1}: {line.strip()}')
"""
    run(f"docker exec -i hub_prod_django python << 'EOF'\n{script2}\nEOF", 'AI COACH CODE LOCATIONS')

    # Find the ai-coach URL pattern
    script3 = """
import os
for root, dirs, files in os.walk('/app'):
    for f in files:
        if f.endswith('.py') and 'url' in f.lower():
            path = os.path.join(root, f)
            with open(path) as fh:
                for i, line in enumerate(fh):
                    if 'ai-coach' in line or 'ai_coach' in line.lower():
                        print(f'{path}:{i+1}: {line.strip()}')
"""
    run(f"docker exec -i hub_prod_django python << 'EOF'\n{script3}\nEOF", 'AI COACH URL PATTERNS')

    # Recipe generator
    script4 = """
import os
for root, dirs, files in os.walk('/app/recipes'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fh:
                content = fh.read()
                if 'generate' in content.lower() or 'openai' in content.lower() or 'groq' in content.lower():
                    print(f'FOUND: {path}')
                    for i, line in enumerate(content.split('\\n')):
                        if any(kw in line.lower() for kw in ['class ', 'def ', 'openai', 'groq', 'generate']):
                            print(f'  L{i+1}: {line.strip()}')
"""
    run(f"docker exec -i hub_prod_django python << 'EOF'\n{script4}\nEOF", 'RECIPE GENERATOR CODE')

    client.close()

if __name__ == "__main__":
    deep_ai_audit()
