import os
import paramiko

def fix_auth_db():
    host = "38.247.138.250"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        # Super admin force
        sql1 = "UPDATE users SET is_superuser=true, is_staff=true, is_active=true, is_verified=true WHERE email='featurekelvin@gmail.com';"
        sql2 = "UPDATE user_roles SET is_active=true WHERE user_id = (SELECT id FROM users WHERE email='featurekelvin@gmail.com');"
        sql3 = "SELECT email, is_superuser, is_active FROM users WHERE email='featurekelvin@gmail.com';"
        
        cmds = [
            f'PGPASSWORD=postgres psql -h 127.0.0.1 -U postgres -d ongozacyberhub -c "{sql1}"',
            f'PGPASSWORD=postgres psql -h 127.0.0.1 -U postgres -d ongozacyberhub -c "{sql2}"',
            f'PGPASSWORD=postgres psql -h 127.0.0.1 -U postgres -d ongozacyberhub -c "{sql3}"'
        ]
        
        for cmd in cmds:
            print(f"--- RUNNING: {cmd[-60:]} ---")
            stdin, stdout, stderr = c.exec_command(cmd)
            stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', 'ignore').strip()
            err = stderr.read().decode('utf-8', 'ignore').strip()
            if out: print("OUT:", out)
            if err and "password" not in err.lower(): print("ERR:", err)
            
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_auth_db()
