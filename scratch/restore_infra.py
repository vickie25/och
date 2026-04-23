import subprocess
import base64
import os
import sys

# 1. Read the local (FIXED) docker-compose.yml
try:
    with open('docker-compose.yml', 'r') as f:
        local_content = f.read()
except Exception as e:
    print(f"Error reading local file: {e}")
    sys.exit(1)

# 2. Prepare the remote restoration script
# This script will run ON THE SERVER via python
# It will write the content directly to the file
b64_content = base64.b64encode(local_content.encode()).decode()

remote_python_script = f"""
import base64
import os

content = base64.b64decode('{b64_content}').decode()
target = '/var/www/och/docker-compose.yml'

try:
    with open(target, 'w') as f:
        f.write(content)
    print("SUCCESS: Infrastructure restored.")
except Exception as e:
    print(f"FAIL: {{e}}")
"""

# 3. Transfer and Execute
b64_script = base64.b64encode(remote_python_script.encode()).decode()
remote_cmd = f"echo {b64_script} | base64 -d | echo 'Ongoza@#1' | sudo -S python3"

print("Initiating total infrastructure restoration (Sudo)...")
result = subprocess.run(['python', 'scripts/ssh_exec.py', remote_cmd], capture_output=True, text=True)

print(result.stdout)
if "SUCCESS" in result.stdout:
    print("Infrastructure file restored. Restarting services...")
    restart_cmd = "cd /var/www/och && echo 'Ongoza@#1' | sudo -S docker-compose up -d --remove-orphans"
    subprocess.run(['python', 'scripts/ssh_exec.py', restart_cmd])
else:
    print(f"Restoration FAILED: {result.stderr}")
