import os
import paramiko

def check_502():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        cmds = [
            f'docker ps -a',
            f'docker logs --tail 50 hub_prod_nextjs',
            f'echo {password} | sudo -S systemctl status nginx --no-pager'
        ]
        
        for cmd in cmds:
            print(f"--- RUNNING: {cmd.split()[-1]} ---")
            stdin, stdout, stderr = c.exec_command(cmd)
            stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', 'ignore').strip()
            err = stderr.read().decode('utf-8', 'ignore').strip()
            if out: print("OUT:\n" + out)
            if err and "password" not in err.lower(): print("ERR:\n" + err)
            
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_502()
