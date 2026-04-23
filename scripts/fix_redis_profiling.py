import os
import paramiko

def fix_redis():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Python script to run on the server to fix the syntax errors properly
    remote_python_patch = """
TARGET = '/var/www/och/backend/fastapi_app/routers/v1/profiling.py'
with open(TARGET, 'r') as f:
    content = f.read()

# Fix the session_ids line
content = content.replace('rc = _get_redis(); session_ids =', 'rc = _get_redis()\\nsession_ids =')
# Fix the delete/srem lines
content = content.replace('rc = _get_redis(); if rc:', 'rc = _get_redis()\\n        if rc:')
# Fix the multi-line f-string at line 815
content = content.replace('result.assessment_summary = f"{gpt_result.get(\\'personalized_message\\', \\'\\')}', 'result.assessment_summary = f\"\"\"{gpt_result.get(\\'personalized_message\\', \\'\\')}')
content = content.replace('AI Analysis: {gpt_result.get(\\'reasoning\\', \\'\\')}\\"', 'AI Analysis: {gpt_result.get(\\'reasoning\\', \\'\\')}\"\"\"')
# Fix the literal \\n that might have been inserted by previous failed sed
content = content.replace('\\\\n', '\\n')

with open(TARGET, 'w') as f:
    f.write(content)
print("PATCHED_SUCCESSFULLY")
"""
    
    print("Uploading python patch script to server...")
    # Escape single quotes for the echo command
    escaped_patch = remote_python_patch.replace("'", "'\\''")
    remote_cmd = f"echo '{escaped_patch}' > /tmp/patch_redis_v2.py"
    client.exec_command(remote_cmd)
    
    print("Executing python patch script via sudo...")
    cmd = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S python3 /tmp/patch_redis_v2.py"
    stdin, stdout, stderr = client.exec_command(cmd)
    print("Output:", stdout.read().decode())
    cmd2 = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker restart hub_prod_fastapi"
    stdin2, stdout2, stderr2 = client.exec_command(cmd2)
    print("Restart Output:", stdout2.read().decode())
    
    # If the file is mounted, the restart is enough. If it's an image build, we must docker cp into it.
    # To be totally safe, we will also copy it into the container.
    print("Copying into container just in case...")
    cmd3 = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker cp /var/www/och/backend/fastapi_app/routers/v1/profiling.py hub_prod_fastapi:/app/routers/v1/profiling.py"
    stdin3, stdout3, stderr3 = client.exec_command(cmd3)
    print("Copy Output:", stdout3.read().decode())
    
    print("Restarting FastAPI container again after copy...")
    cmd4 = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker restart hub_prod_fastapi"
    stdin4, stdout4, stderr4 = client.exec_command(cmd4)
    print("Final Restart Output:", stdout4.read().decode())
    
    client.close()

if __name__ == "__main__":
    fix_redis()
