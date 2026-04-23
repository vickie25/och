import subprocess
import base64
import os
import sys

# 1. Read the local FIXED docker-compose.yml
with open('docker-compose.yml', 'r') as f:
    content = f.read()

# 2. Encode and Split
b64_content = base64.b64encode(content.encode()).decode()
CHUNK_SIZE = 500  # Safe size for any shell buffer
chunks = [b64_content[i:i+CHUNK_SIZE] for i in range(0, len(b64_content), CHUNK_SIZE)]

print(f"Restoring infrastructure in {len(chunks)} chunks...")

# 3. Clear remote temp file
subprocess.run(['python', 'scripts/ssh_exec.py', '> /tmp/compose_b64.txt'], capture_output=True)

# 4. Transfer chunks
for i, chunk in enumerate(chunks):
    print(f"Transferring chunk {i+1}/{len(chunks)}...")
    cmd = f'echo "{chunk}" >> /tmp/compose_b64.txt'
    subprocess.run(['python', 'scripts/ssh_exec.py', cmd], capture_output=True)

# 5. Decode and Move to Production
print("Stitching infrastructure backbone...")
stitch_cmd = "cat /tmp/compose_b64.txt | tr -d ' \\n\\r' | base64 -d | echo 'Ongoza@#1' | sudo -S tee /var/www/och/docker-compose.yml > /dev/null"
result = subprocess.run(['python', 'scripts/ssh_exec.py', stitch_cmd], capture_output=True, text=True)

if result.returncode == 0:
    print("SUCCESS: Infrastructure restored.")
    # Restart services
    print("Rebooting ecosystem...")
    restart_cmd = "cd /var/www/och && echo 'Ongoza@#1' | sudo -S docker-compose up -d --remove-orphans"
    subprocess.run(['python', 'scripts/ssh_exec.py', restart_cmd])
else:
    print(f"FAILED: {result.stderr}")
