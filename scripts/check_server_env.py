import os
import paramiko

def check_env():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # We check both the host .env file and the container's environment variables
        cmds = [
            f'echo "{password}" | sudo -S cat /var/www/och/.env | grep -i DB_',
            f'echo "{password}" | sudo -S docker exec hub_prod_django env | grep -i DB_'
        ]
        
        for cmd in cmds:
            print(f"--- RUNNING: {cmd.split('| sudo')[1]} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode('utf-8', 'ignore')
            print(out.strip() if out else "No output")
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_env()
