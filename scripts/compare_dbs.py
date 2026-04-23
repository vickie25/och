import os
import paramiko
import sys

def compare_dbs():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [LOCAL DB USER COUNT] ---")
        command = "sudo docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c 'SELECT COUNT(*) FROM users'"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        print("\n--- [REMOTE DB USER COUNT] ---")
        # Note: We use PGPASSWORD here to connect to the remote server
        command = "PGPASSWORD=postgres psql -h 38.247.138.250 -U postgres -d ongozacyberhub -c 'SELECT COUNT(*) FROM users'"
        stdin, stdout, stderr = client.exec_command(command)
        print(f"STDOUT: {stdout.read().decode('utf-8', 'ignore')}")
        print(f"STDERR: {stderr.read().decode('utf-8', 'ignore')}")

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    compare_dbs()
