import os
import paramiko
import sys

def read_compose_robust():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [READING DOCKER COMPOSE] ---")
        # Use cat and read from stdout buffer
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" cat /var/www/och/docker-compose.yml', get_pty=True)
        content = stdout.read().decode('utf-8', 'ignore')
        
        # Save to a local file for inspection if needed, but for now just print relevant parts
        if "django:" in content:
            print("Found Django service section.")
            # Print the whole content for the model to see
            print(content)
        else:
            print("Django section not found in the output.")
            
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    read_compose_robust()
