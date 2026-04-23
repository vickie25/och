import os
import paramiko

def inject_groq_key():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    key = os.environ.get('GROQ_API_KEY', '')
    
    # Inject into hub_prod_django
    print("Injecting into Django...")
    client.exec_command(f'docker exec hub_prod_django bash -c "echo \\"GROQ_API_KEY={key}\\" >> /app/.env"')
    
    # Inject into hub_prod_fastapi
    print("Injecting into FastAPI...")
    client.exec_command(f'docker exec hub_prod_fastapi bash -c "echo \\"GROQ_API_KEY={key}\\" >> /app/.env"')
    
    # Verify (without showing the full key)
    stdin, stdout, stderr = client.exec_command('docker exec hub_prod_django grep GROQ_API_KEY /app/.env')
    print(f"Django Verification: {stdout.read().decode().strip()[:20]}...")
    
    client.close()

if __name__ == "__main__":
    inject_groq_key()
