import os
import paramiko

def check_status():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=10)
        
        cmds = [
            f'echo {password} | sudo -S docker ps --format "{{{{.Names}}}} | {{{{.Image}}}} | {{{{.Status}}}}"',
            f'echo {password} | sudo -S grep "DB_HOST" /var/www/och/.env'
        ]
        
        for cmd in cmds:
            print(f"-- RUNNING --")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode().strip()
            if out: print(out)
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_status()
