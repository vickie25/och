import os
import paramiko
import sys

def read_fastapi_server_config():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [SERVER docker-compose.yml: FASTAPI SERVICE] ---")
        command = "sudo cat /var/www/och/docker-compose.yml"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        content = stdout.read().decode('utf-8', 'ignore')
        
        # Extract the fastapi part specifically
        import re
        match = re.search(r"fastapi:.*?(?=\n\n|\n  \w+:|$)", content, re.DOTALL)
        if match:
            print(match.group(0))
        else:
            # Fallback: print lines around fastapi
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if "fastapi:" in line:
                    print("\n".join(lines[max(0, i-5):min(len(lines), i+30)]))
                    break
            
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    read_fastapi_server_config()
