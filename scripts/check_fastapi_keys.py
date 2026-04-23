import os
import paramiko

def check_fastapi_keys():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    stdin, stdout, stderr = client.exec_command('docker exec hub_prod_fastapi env')
    env = stdout.read().decode()
    
    for line in sorted(env.splitlines()):
        low = line.lower()
        if any(kw in low for kw in ['openai', 'gpt', 'groq', 'api_key', 'model', 'redis', 'llm', 'fastapi']):
            print(line)
    
    # Also check NextJS env
    stdin, stdout, stderr = client.exec_command('docker exec hub_prod_nextjs env')
    env2 = stdout.read().decode()
    print("\n--- NEXTJS FASTAPI ENV ---")
    for line in sorted(env2.splitlines()):
        low = line.lower()
        if any(kw in low for kw in ['fastapi', 'profil', 'ai_']):
            print(line)
    
    client.close()

if __name__ == "__main__":
    check_fastapi_keys()
