import os
import paramiko

def audit_logs():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        cmds = [
            f'echo {password} | sudo -S docker logs --tail 200 hub_prod_django',
            f'echo {password} | sudo -S docker logs --tail 200 hub_prod_nextjs'
        ]
        
        for cmd in cmds:
            print(f"--- LOGS FOR: {cmd.split()[-1]} ---")
            stdin, stdout, stderr = c.exec_command(cmd)
            stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', 'ignore')
            err = stderr.read().decode('utf-8', 'ignore')
            
            # Print only lines containing Error, Traceback, Exception, 500
            for line in (out + err).split('\n'):
                line_lower = line.lower()
                if "error" in line_lower or "traceback" in line_lower or "exception" in line_lower or "500" in line_lower or "auth" in line_lower:
                    print(line.strip())
            print("\n")
            
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    audit_logs()
