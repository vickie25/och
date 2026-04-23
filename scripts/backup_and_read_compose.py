import os
import paramiko
import sys

def backup_and_read_compose():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [BACKING UP AND READING SERVER docker-compose.yml] ---")
        # Read the file
        command = "sudo cat /var/www/och/docker-compose.yml"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        content = stdout.read().decode('utf-8', 'ignore')
        
        # Save it to a temporary file on the user's machine for me to analyze
        # Actually I'll just print it in chunks if it's too large, but 263 lines is fine.
        print(content)
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    backup_and_read_compose()
