import os
import paramiko

def configure_firewall():
    host = "38.247.138.250"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=10)
        
        # 1. Firewall rules
        ufw_cmds = [
            'sudo ufw --force enable',
            'sudo ufw allow 22/tcp',
            'sudo ufw allow from 69.30.235.220 to any port 5432',
            'sudo ufw status'
        ]
        
        # 2. Postgres config
        # Find postgres version
        stdin, stdout, stderr = client.exec_command('ls /etc/postgresql/')
        pg_versions = stdout.read().decode().split()
        if pg_versions:
            pg_ver = pg_versions[0]
            pg_cmds = [
                f'echo "listen_addresses = \'*\'" | sudo tee -a /etc/postgresql/{pg_ver}/main/postgresql.conf',
                f'echo "host all all 69.30.235.220/32 md5" | sudo tee -a /etc/postgresql/{pg_ver}/main/pg_hba.conf',
                f'sudo systemctl restart postgresql'
            ]
        else:
            pg_cmds = []
            print("No /etc/postgresql/ versions found.")

        cmds = ufw_cmds + pg_cmds
        
        for cmd in cmds:
            print(f"--- RUNNING: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(f"echo {password} | sudo -S {cmd}" if "sudo " in cmd else cmd)
            print(stdout.read().decode('utf-8', 'ignore'))
            err = stderr.read().decode('utf-8', 'ignore')
            if err and "password" not in err.lower():
                print("ERR:", err)
                
        client.close()
    except Exception as e:
        print(f"FAILED on {host}: {e}")

if __name__ == "__main__":
    configure_firewall()
