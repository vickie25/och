import os
import paramiko

def bring_all_back():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        cmds = [
            f'cd /var/www/och && echo {password} | sudo -S docker-compose up -d django fastapi nextjs'
        ]
        
        for cmd in cmds:
            print(f"--- RUNNING ---")
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
    bring_all_back()
