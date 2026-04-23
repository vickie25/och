import os
import paramiko

def finalize_switch():
    host_220 = "69.30.235.220"
    host_250 = "38.247.138.250"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c220 = paramiko.SSHClient()
        c220.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c220.connect(host_220, username=user, password=password, timeout=10)
        
        cmds = [
            # 1. Stop app containers to prevent data mutation during the final switch
            'echo "Stopping containers..."',
            f'cd /var/www/och && echo {password} | sudo -S docker-compose stop nextjs fastapi django',
            
            # 2. Final data sync from postgres-relational -> 38.247.138.250
            'echo "Final data sync..."',
            # Clear 250 DB
            f'PGPASSWORD=postgres psql -h {host_250} -U postgres -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=\'ongozacyberhub\';" || true',
            f'PGPASSWORD=postgres psql -h {host_250} -U postgres -d postgres -c "DROP DATABASE IF EXISTS ongozacyberhub;" || true',
            f'PGPASSWORD=postgres psql -h {host_250} -U postgres -d postgres -c "CREATE DATABASE ongozacyberhub;"',
            # Transfer
            f'echo {password} | sudo -S docker exec -e PGPASSWORD=postgres hub_prod_postgres bash -c "pg_dump -U postgres ongozacyberhub | psql -q -h {host_250} -U postgres -d ongozacyberhub"',
            
            # 3. Update pointer
            'echo "Updating .env config..."',
            f'echo {password} | sudo -S sed -i "s/DB_HOST=postgres-relational/DB_HOST={host_250}/g" /var/www/och/.env',
            
            # 4. Remove local Postgres from docker-compose.yml (optional but clean)
            #'cd /var/www/och && echo {password} | sudo -S sed -i "/  postgres:/,+25d" docker-compose.yml', 
            
            # 5. Restart apps
            'echo "Bringing applications online..."',
            f'cd /var/www/och && echo {password} | sudo -S docker-compose up -d'
        ]
        
        for cmd in cmds:
            print(f"-- RUNNING --")
            stdin, stdout, stderr = c220.exec_command(cmd)
            stdout.channel.recv_exit_status()  # Wait for completion
            out = stdout.read().decode()
            if out: print('OUT:', out[:500])
            err = stderr.read().decode()
            if err and "password" not in err.lower() and "sudo" not in err.lower(): print('ERR:', err[:500])
        
        c220.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    finalize_switch()
