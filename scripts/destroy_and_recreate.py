import os
import paramiko

def destroy_and_recreate():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        cmds = [
            # Kill containers forcefully
            f'echo {password} | sudo -S docker stop hub_prod_django hub_prod_fastapi hub_prod_nextjs',
            f'echo {password} | sudo -S docker rm hub_prod_django hub_prod_fastapi hub_prod_nextjs',
            
            # Restart from compose
            f'cd /var/www/och && echo {password} | sudo -S docker-compose up -d django fastapi nextjs',
            
            f'echo {password} | sudo -S docker ps --format "{{{{.Names}}}} {{{{.Image}}}} {{{{.CreatedAt}}}}" | grep hub_prod_django'
        ]
        
        for cmd in cmds:
            print(f"--- RUNNING: {cmd.split()[-1]} ---")
            stdin, stdout, stderr = c.exec_command(cmd)
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            if out: print("OUT:", out)
            if err and "password" not in err.lower(): print("ERR:", err)
            
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    destroy_and_recreate()
