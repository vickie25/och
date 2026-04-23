import os
import paramiko

def check_250_tables():
    host = "38.247.138.250"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        cmd = f'PGPASSWORD=postgres psql -U postgres -d ongozacyberhub -c "\dt public.*"'
        
        stdin, stdout, stderr = c.exec_command(cmd)
        out = stdout.read().decode().strip()
        print(out)
        
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_250_tables()
