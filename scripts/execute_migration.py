import os
import paramiko
import time

def execute_migration():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    remote_db = "38.247.138.250"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=10)
        
        cmds = [
            # 1. Maintenance Mode
            'echo "Stopping containers..."',
            f'cd /var/www/och && echo {password} | sudo -S docker-compose stop nextjs fastapi django',
            
            # 2. Cleanup existing DB on .250 if any (dropping connections first)
            'echo "Preparing remote database..."',
            f'PGPASSWORD=postgres psql -h {remote_db} -U postgres -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=\'ongozacyberhub\';" || true',
            f'PGPASSWORD=postgres psql -h {remote_db} -U postgres -d postgres -c "DROP DATABASE IF EXISTS ongozacyberhub;" || true',
            
            # 3. Data Transfer
            'echo "Migrating data from local container to .250..."',
            f'echo {password} | sudo -S docker exec hub_prod_postgres pg_dump -U postgres --clean --create ongozacyberhub | PGPASSWORD=postgres psql -h {remote_db} -U postgres -d postgres',
            
            # 4. App configuration
            'echo "Updating .env..."',
            f'echo {password} | sudo -S sed -i "s/DB_HOST=postgres-relational/DB_HOST=38.247.138.250/g" /var/www/och/.env',
            
            # 5. Restart
            'echo "Restarting services..."',
            f'cd /var/www/och && echo {password} | sudo -S docker-compose up -d'
        ]
        
        for cmd in cmds:
            print(f"--- RUNNING ---")
            stdin, stdout, stderr = client.exec_command(f"echo {password} | sudo -S {cmd}" if "sudo " in cmd and "sudo -S docker" not in cmd else cmd)
            out = stdout.read().decode('utf-8', 'ignore')
            err = stderr.read().decode('utf-8', 'ignore')
            if out: print("OUT:", out.strip()[:1000])
            if err and "password" not in err.lower() and "sudo" not in err.lower(): print("ERR:", err.strip()[:1000])
                
        client.close()
    except Exception as e:
        print(f"FAILED on {host}: {e}")

if __name__ == "__main__":
    execute_migration()
