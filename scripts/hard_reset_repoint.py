import paramiko
import os

def hard_reset_repoint():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        # Upload corrected remote_production.env
        print("Uploading corrected .env to /var/www/och/.env...")
        sftp = c.open_sftp()
        sftp.put('remote_production.env', '/tmp/remote_production.env')
        sftp.put('remote_docker-compose.yml', '/tmp/remote_docker-compose.yml')
        sftp.close()
        
        cmds = [
            f'echo {password} | sudo -S mv /tmp/remote_production.env /var/www/och/.env',
            f'echo {password} | sudo -S mv /tmp/remote_docker-compose.yml /var/www/och/docker-compose.yml',
            
            # Hard Restart
            'echo "Force recreating containers..."',
            f'cd /var/www/och && echo {password} | sudo -S docker-compose down',
            f'cd /var/www/och && echo {password} | sudo -S docker-compose up -d --force-recreate',
            
            # Verify DB_HOST
            f'echo {password} | sudo -S docker exec hub_prod_django env | grep DB_HOST'
        ]
        
        for cmd in cmds:
            print(f"--- RUNNING ---")
            stdin, stdout, stderr = c.exec_command(cmd)
            stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', 'ignore').strip()
            print("OUT:", out)
            
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    hard_reset_repoint()
