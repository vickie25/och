import os
import paramiko
import time

def secure_restart():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        cmds = [
            f'cd /var/www/och && echo {password} | sudo -S docker-compose stop django fastapi nextjs',
            f'cd /var/www/och && echo {password} | sudo -S docker-compose rm -f django fastapi nextjs',
            f'cd /var/www/och && echo {password} | sudo -S sed -i "s/DB_HOST=postgres-relational/DB_HOST=38.247.138.250/g" .env',
            f'cd /var/www/och && echo {password} | sudo -S cat .env | grep DB_HOST',
            f'cd /var/www/och && echo {password} | sudo -S docker-compose up -d django fastapi nextjs',
            f'echo {password} | sudo -S docker ps | grep hub_prod'
        ]
        
        for cmd in cmds:
            print(f"--- RUNNING: {cmd.split('sudo -S ')[-1]} ---")
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
    secure_restart()
