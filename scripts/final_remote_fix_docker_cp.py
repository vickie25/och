import os
import paramiko
import sys

def final_remote_fix_docker_cp():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [DOCKER CP & EXEC REPAIR] ---")
        logic_file = "/tmp/final_repair_logic.py"
        target_in_container = "/app/final_repair_logic.py"
        
        # 1. Copy file into container
        command = f"sudo docker cp {logic_file} hub_prod_django:{target_in_container}"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print("Copied logic file into container.")
        
        # 2. Execute it
        command = f"sudo docker exec hub_prod_django python3 {target_in_container}"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    final_remote_fix_docker_cp()
