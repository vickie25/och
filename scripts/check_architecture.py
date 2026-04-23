import os
import paramiko

def check_architecture():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # Check running containers and docker-compose context
        cmds = [
            f'echo "{password}" | sudo -S docker ps --format "{{{{.Names}}}} | {{{{.Image}}}} | {{{{.Status}}}}"',
        ]
        
        for cmd in cmds:
            print(f"--- RUNNING COMMAND ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode('utf-8', 'ignore')
            print(out.strip() if out else "No output")
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_architecture()
