import paramiko

def patch_nextjs_timeout():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Path in container: /app/app/api/profiling/session/start/route.ts
    patch_script = """
import os
path = '/app/app/api/profiling/session/start/route.ts'
if os.path.exists(path):
    with open(path, 'r') as f:
        content = f.read()
    
    # Increase timeout to 15 seconds
    new_content = content.replace('AbortSignal.timeout(5000)', 'AbortSignal.timeout(15000)')
    
    with open(path, 'w') as f:
        f.write(new_content)
    print('Next.js Profiler timeout increased to 15s.')
else:
    print('ERROR: Route file not found in container.')
"""
    client.exec_command(f"docker exec -i hub_prod_nextjs python3 << 'EOF'\n{patch_script}\nEOF")
    client.close()

if __name__ == "__main__":
    patch_nextjs_timeout()
