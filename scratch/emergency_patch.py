import subprocess
import base64
import os

# Content of the fixed docker-compose.yml
with open('docker-compose.yml', 'r') as f:
    content = f.read()

# Base64 encode the content
b64_content = base64.b64encode(content.encode()).decode()

# Command to run on the server
# We use sudo tee to ensure permissions are handled correctly and to bypass shell parsing issues
remote_cmd = f"echo {b64_content} | base64 -d | echo 'Ongoza@#1' | sudo -S tee /var/www/och/docker-compose.yml > /dev/null"

# Execute via ssh_exec.py
print(f"Transferring fixed docker-compose.yml to server...")
result = subprocess.run(['python', 'scripts/ssh_exec.py', remote_cmd], capture_output=True, text=True)

if result.returncode == 0:
    print("SUCCESS: File transferred.")
    # Verify the line specifically
    verify_cmd = "sed -n '216p' /var/www/och/docker-compose.yml"
    v_result = subprocess.run(['python', 'scripts/ssh_exec.py', verify_cmd], capture_output=True, text=True)
    print(f"Verification (Line 216): {v_result.stdout.strip()}")

    # Now restart the services
    print("Restarting FastAPI and Nginx...")
    restart_cmd = "cd /var/www/och && echo 'Ongoza@#1' | sudo -S docker-compose up -d --force-recreate fastapi nginx"
    subprocess.run(['python', 'scripts/ssh_exec.py', restart_cmd])
else:
    print(f"FAILED: {result.stderr}")
