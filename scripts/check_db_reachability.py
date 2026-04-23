import os
import paramiko
import sys

def check_remote_db_reachable():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [REMOTE DB REACHABILITY CHECK] ---")
        command = "nc -zv 38.247.138.250 5432"
        stdin, stdout, stderr = client.exec_command(command)
        print(f"STDOUT: {stdout.read().decode('utf-8', 'ignore')}")
        print(f"STDERR: {stderr.read().decode('utf-8', 'ignore')}")
        
        print("\n--- [LOCAL DB REACHABILITY CHECK] ---")
        command = "sudo docker exec hub_prod_django ping -c 1 postgres-relational"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_remote_db_reachable()
