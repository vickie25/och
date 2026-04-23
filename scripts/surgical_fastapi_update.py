import os
import paramiko
import sys

def surgical_fastapi_update():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    correct_fastapi_service = """  fastapi:
    image: ghcr.io/cresdynamics-lang/och-fastapi:latest
    container_name: hub_prod_fastapi
    environment:
      REDIS_URL: redis://redis:6379/1
      VECTOR_DB_HOST: postgres-vector
      VECTOR_DB_PORT: 5432
      VECTOR_DB_NAME: ${VECTOR_POSTGRES_DB:-ongozacyberhub_vector}
      VECTOR_DB_USER: ${POSTGRES_USER:-postgres}
      VECTOR_DB_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      DJANGO_API_URL: http://django:8000
      CORS_ORIGINS: '["http://localhost:3000","https://cybochengine.africa"]'
      JWT_SECRET_KEY: psd3zhcbrDdxzbzDsZW9NeavR_wLXLP3S_LD4kNc5kk
      LOG_LEVEL: ${LOG_LEVEL:-info}
    volumes:
      - ./backend/fastapi_app:/app
    depends_on:
      postgres-vector:
        condition: service_healthy
      django:
        condition: service_healthy
    networks:
      - ongoza-network
    restart: unless-stopped
    command: sh -c "pip install -r /app/requirements.txt --quiet --no-cache-dir 2>/dev/null || true && uvicorn main:app --host 0.0.0.0 --port 8001 --workers ${FASTAPI_WORKERS:-2} --log-level ${FASTAPI_LOG_LEVEL:-info} --timeout-keep-alive 5"
    mem_limit: ${FASTAPI_MEM_LIMIT:-800m}
    cpus: ${FASTAPI_CPUS:-1.0}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
"""

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [SURGICAL FASTAPI UPDATE] ---")
        
        # Read the file
        command = "sudo cat /var/www/och/docker-compose.yml"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        content = stdout.read().decode('utf-8', 'ignore')
        
        # Find fastapi: section and replace it
        import re
        # Find fastapi block until the next top-level service or end of file
        # We look for a line starting with 2 spaces and name: or a comment
        pattern = r"  fastapi:.*?(?=\n  \w+:|\n\n|\n$)"
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, correct_fastapi_service.rstrip(), content, flags=re.DOTALL)
            print("Found and Replaced existing FastAPI service definition.")
            
            # Write back
            client.exec_command(f"cat << 'EOF' > /tmp/docker-compose.fixed.yml\n{new_content}\nEOF")
            command = "sudo mv /tmp/docker-compose.fixed.yml /var/www/och/docker-compose.yml"
            stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
            
            # Restart
            print("Restarting FastAPI service with correct host/port binding...")
            command = "sudo docker compose -f /var/www/och/docker-compose.yml up -d fastapi"
            stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
            print(stdout.read().decode('utf-8', 'ignore'))
        else:
            print("ERROR: Could not find '  fastapi:' block to replace.")
            
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    surgical_fastapi_update()
