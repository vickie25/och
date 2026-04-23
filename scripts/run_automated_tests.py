import os
import paramiko
import json
import time

def run_automated_tests():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    print("Connecting to server...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=10)
        
        # 1. Get an access token for kelvin2o2maina@gmail.com
        print("\n--- Generating Authentication Token ---")
        token_cmd = """echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_django python manage.py shell -c "from users.models import User; from rest_framework_simplejwt.tokens import RefreshToken; u = User.objects.first(); print(str(RefreshToken.for_user(u).access_token) if u else 'USER_NOT_FOUND')"
        """
        stdin, stdout, stderr = client.exec_command(token_cmd)
        output = stdout.read().decode().strip()
        lines = [line for line in output.split('\n') if not line.startswith('[sudo]') and line.strip()]
        token = lines[-1] if lines else None
        
        if not token or token == 'USER_NOT_FOUND':
            print("Failed to get token!")
            print("Output:", output)
            return
            
        print("Token retrieved successfully.")
        
        # 2. Test AI Profiler (FastAPI directly)
        print("\n--- Testing AI Profiler (FastAPI Internally) ---")
        profiler_cmd = f"""echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_django curl -sv -X POST http://fastapi:8001/api/v1/profiling/session/start -H "Authorization: Bearer {token}" -H "Content-Type: application/json" -d '{{}}'"""
        stdin, stdout, stderr = client.exec_command(profiler_cmd)
        prof_out = stdout.read().decode().strip()
        prof_err = stderr.read().decode().strip()
        print("Response:", prof_out[:500])
        print("Error/Header Output:", prof_err[:1000])
        
        # 3. Test AI Coach (Django via Nginx)
        print("\n--- Testing AI Coach (Django via Nginx) ---")
        coach_cmd = f"""curl -s -X POST https://cybochengine.africa/api/v1/coaching/ai-coach/chat -H "Authorization: Bearer {token}" -H "Content-Type: application/json" -d '{{\"message\": \"Hello, can you help me?\"}}'"""
        stdin, stdout, stderr = client.exec_command(coach_cmd)
        coach_out = stdout.read().decode().strip()
        print("Response:", coach_out[:500])
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_automated_tests()
