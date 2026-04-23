import os
import paramiko
import sys

def find_traceback_systematic():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [SEARCHING FOR Traceback IN ALL LOGS] ---")
        # Search for Traceback in the full log output
        command = "sudo docker logs hub_prod_django 2>&1 | grep -A 30 'Traceback' | tail -n 100"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    find_traceback_systematic()
