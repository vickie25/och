import os
import paramiko

def check_env_cache():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        cmds = [
            f'cat /var/www/och/docker-compose.yml | grep DB_HOST',
            f'cat /var/www/och/.env | grep DB_HOST',
            f'docker ps --format "{{{{.Names}}}} {{{{.Image}}}} {{{{.CreatedAt}}}}"',
            f'docker exec hub_prod_django ps aux'
        ]
        
        for cmd in cmds:
            print(f"--- RUNNING: {cmd.split('/')[-1]} ---")
            stdin, stdout, stderr = c.exec_command(f'echo {password} | sudo -S {cmd}' if 'sudo ' in cmd else cmd)
            out = stdout.read().decode().strip()
            print("OUT:", out)
            
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_env_cache()
