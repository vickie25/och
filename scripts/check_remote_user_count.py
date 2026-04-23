import os
import paramiko
import sys

def check_remote_user_count_script():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [CHECKING REMOTE USER COUNT] ---")
        # Direct psql from within the postgres container to the remote host
        sql = "SELECT COUNT(*) FROM users"
        command = f"sudo docker exec hub_prod_postgres psql -h 38.247.138.250 -U postgres -d ongozacyberhub -c \"{sql}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_remote_user_count_script()
