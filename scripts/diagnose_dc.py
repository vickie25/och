import os
import paramiko

def diagnose_docker_compose():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        cmds = [
            f'cd /var/www/och && echo {password} | sudo -S docker-compose config',
            f'cd /var/www/och && echo {password} | sudo -S docker-compose ps'
        ]
        
        for cmd in cmds:
            print(f"--- RUNNING: {cmd.split()[-1]} ---")
            stdin, stdout, stderr = c.exec_command(cmd)
            stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', 'ignore').strip()
            err = stderr.read().decode('utf-8', 'ignore').strip()
            if err and "password" not in err.lower(): print("ERR:\n" + err)
            elif "config" not in cmd: print("OUT:\n" + out) # print all out for ps, config is too big unless there is error
            if "config" in cmd and err: print("CONFIG HAS ERROR")
            
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diagnose_docker_compose()
