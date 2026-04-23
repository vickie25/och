import os
import paramiko
import sys

def remote_db_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    remote_host = "38.247.138.250"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print(f"\n--- [REMOTE DB AUDIT: {remote_host}] ---")
        # List tables on the remote DB
        command = f"PGPASSWORD=postgres psql -h {remote_host} -U postgres -d ongozacyberhub -c '\\dt public.*'"
        stdin, stdout, stderr = client.exec_command(command)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    remote_db_audit()
