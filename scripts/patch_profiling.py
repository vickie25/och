import os
import paramiko

def patch_profiling():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))

    # Step 1: Read the current file to verify the exact line we're patching
    print("Step 1: Verifying target line on production...")
    stdin, stdout, stderr = client.exec_command(
        "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_fastapi "
        "grep -n 'return result' /app/routers/v1/profiling.py"
    )
    output = stdout.read().decode('utf-8', errors='replace')
    print(output)

    # Step 2: Use sed to add _save_session(session) before the specific "return result" 
    # that follows the portfolio entry creation block.
    # We target the exact pattern: line with "# Don't fail the entire completion" 
    # followed by empty line, followed by "return result"
    print("Step 2: Patching profiling.py...")
    # Use a Python one-liner inside the container to do a precise replacement
    patch_cmd = (
        "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_fastapi "
        "python3 -c \""
        "import re; "
        "f = open('/app/routers/v1/profiling.py', 'r'); content = f.read(); f.close(); "
        "old = '            # Don\\'t fail the entire completion if portfolio creation fails\\n\\n        return result'; "
        "new = '            # Don\\'t fail the entire completion if portfolio creation fails\\n\\n        _save_session(session)\\n        return result'; "
        "assert old in content, 'Target pattern not found!'; "
        "content = content.replace(old, new, 1); "
        "f = open('/app/routers/v1/profiling.py', 'w'); f.write(content); f.close(); "
        "print('Patch applied successfully')"
        "\""
    )
    stdin, stdout, stderr = client.exec_command(patch_cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip() and 'password' not in err.lower():
        print("STDERR:", err)

    # Step 3: Verify the patch was applied
    print("Step 3: Verifying patch...")
    stdin, stdout, stderr = client.exec_command(
        "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_fastapi "
        "grep -n '_save_session' /app/routers/v1/profiling.py"
    )
    output = stdout.read().decode('utf-8', errors='replace')
    print(output)

    # Step 4: Restart FastAPI
    print("Step 4: Restarting FastAPI container...")
    stdin, stdout, stderr = client.exec_command(
        "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker restart hub_prod_fastapi"
    )
    print(stdout.read().decode('utf-8', errors='replace'))
    print(stderr.read().decode('utf-8', errors='replace'))

    # Step 5: Wait and verify health
    import time
    print("Step 5: Waiting 8 seconds for container to start...")
    time.sleep(8)
    stdin, stdout, stderr = client.exec_command(
        "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_fastapi "
        "python3 -c \"import urllib.request; r = urllib.request.urlopen('http://localhost:8100/health'); print('Health:', r.status, r.read().decode())\""
    )
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip() and 'password' not in err.lower():
        print("Health check error:", err)

    print("DONE.")
    client.close()

if __name__ == "__main__":
    patch_profiling()
