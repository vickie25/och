import os
import paramiko

def execute_retransfer():
    host_220 = "69.30.235.220"
    host_250 = "38.247.138.250"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    # 1. Setup DB on .250
    try:
        c250 = paramiko.SSHClient()
        c250.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c250.connect(host_250, username=user, password=password, timeout=10)
        
        print("--- RUNNING ON .250: PREPARING DB ---")
        cmds = [
            f'PGPASSWORD=postgres psql -U postgres -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=\'ongozacyberhub\';"',
            f'PGPASSWORD=postgres psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS ongozacyberhub;"',
            f'PGPASSWORD=postgres psql -U postgres -d postgres -c "CREATE DATABASE ongozacyberhub;"'
        ]
        
        for cmd in cmds:
            c250.exec_command(cmd)
        c250.close()
    except Exception as e:
        print(f"Error on .250: {e}")

    # 2. Extract and transfer from .220
    try:
        c220 = paramiko.SSHClient()
        c220.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c220.connect(host_220, username=user, password=password, timeout=10)
        
        print("--- RUNNING ON .220: TRANSFERRING OVER NETWORK ---")
        cmd = f'echo {password} | sudo -S docker exec -e PGPASSWORD=postgres hub_prod_postgres bash -c "pg_dump -U postgres ongozacyberhub | psql -h {host_250} -U postgres -d ongozacyberhub"'
        
        stdin, stdout, stderr = c220.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        print(out)
        if err and "password" not in err.lower(): print("ERR:", err)
        c220.close()
    except Exception as e:
        print(f"Error on .220: {e}")

if __name__ == "__main__":
    execute_retransfer()
