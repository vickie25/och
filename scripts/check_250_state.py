import os
import paramiko

def check_250_state():
    host = "38.247.138.250"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=10)
        
        cmds = [
            'sudo ufw status',
            'docker ps',
            'which psql',
            'sudo systemctl status postgresql --no-pager',
            'PGPASSWORD=postgres psql -U postgres -d ongozacyberhub -c "\dt public.*" || true'
        ]
        
        for cmd in cmds:
            print(f"--- RUNNING: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(f"echo {password} | sudo -S {cmd}" if "sudo" in cmd else cmd)
            print(stdout.read().decode('utf-8', 'ignore'))
            err = stderr.read().decode('utf-8', 'ignore')
            if err and "password" not in err.lower():
                print("ERR:", err)
                
        client.close()
    except Exception as e:
        print(f"FAILED on {host}: {e}")

if __name__ == "__main__":
    check_250_state()
