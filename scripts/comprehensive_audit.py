import os
import paramiko

def comprehensive_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    db_host = "38.247.138.250"
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        print("======== 1. DJANGO TRACEBACK ========")
        # Get the last 300 lines of django to catch the traceback
        stdin, stdout, stderr = c.exec_command(f'echo {password} | sudo -S docker logs --tail 300 hub_prod_django')
        stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'ignore')
        err = stderr.read().decode('utf-8', 'ignore')
        
        traceback_lines = []
        is_traceback = False
        for line in (out + err).split('\n'):
            if "Traceback" in line or "Exception" in line or "Internal Server Error" in line or "OperationalError" in line:
                is_traceback = True
            if is_traceback:
                traceback_lines.append(line.strip())
            if is_traceback and not line.strip() and len(traceback_lines) > 5:
                # empty line usually ends standard traceback block
                is_traceback = False
                
        # Keep just the bottom-most tracebacks to avoid huge spam
        if traceback_lines:
            print("\n".join(traceback_lines[-40:])) # last 40 lines of the trace
        else:
            print("No tracebacks found in the last 300 lines.")
            
        print("\n======== 2. DB QUERY (featurekelvin@gmail.com) ========")
        # Test direct query from .220 to .250 using psql inside hub_prod_postgres
        sql = "SELECT email, is_active, is_superuser FROM users WHERE email='featurekelvin@gmail.com';"
        test_cmd = f'echo {password} | sudo -S docker exec -e PGPASSWORD=postgres hub_prod_postgres psql -h {db_host} -U postgres -d ongozacyberhub -c "{sql}"'
        stdin, stdout, stderr = c.exec_command(test_cmd)
        stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'ignore')
        print(out.strip() if out else stderr.read().decode('utf-8', 'ignore'))
        
        print("\n======== 3. DB CONNECTION TEST ========")
        # Just check if Django config says it's pointing to .250
        env_cmd = f'echo {password} | sudo -S docker exec hub_prod_django env | grep DB_HOST'
        stdin, stdout, stderr = c.exec_command(env_cmd)
        stdout.channel.recv_exit_status()
        print("DJANGO ENV REF:", stdout.read().decode().strip())

        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    comprehensive_audit()
