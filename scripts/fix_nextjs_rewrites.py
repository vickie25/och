import os
import paramiko
import time

def fix_nextjs_rewrites():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        cmds = [
            f'echo {password} | sudo -S docker exec hub_prod_nextjs sed -i "s|https://cybochengine.africa/api|http://django:8000|g" .next/routes-manifest.json',
            f'cd /var/www/och && echo {password} | sudo -S docker-compose restart nextjs'
        ]
        
        for cmd in cmds:
            print(f"--- RUNNING ---")
            stdin, stdout, stderr = c.exec_command(cmd)
            stdout.channel.recv_exit_status()
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            if out: print("OUT:", out)
            if err and "password" not in err.lower(): print("ERR:", err)
            
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_nextjs_rewrites()
