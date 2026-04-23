import os
import paramiko

def verify_django_repoint():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        cmds = [
            f'echo {password} | sudo -S docker exec hub_prod_django env | grep DB_HOST'
        ]
        
        for cmd in cmds:
            print(f"--- RUNNING ---")
            stdin, stdout, stderr = c.exec_command(cmd)
            stdout.channel.recv_exit_status()
            out = stdout.read().decode().strip()
            print("OUT:", out)
            
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_django_repoint()
