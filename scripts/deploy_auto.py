import paramiko
import sys
import time

def deploy():
    # Production Server Details
    host = '69.30.235.220'
    port = 22
    username = 'administrator'
    password = 'Ongoza@#1'
    project_root = '/var/www/och'

    try:
        print(f"Connecting to {host} via SSH...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port, username, password, timeout=30)
        print("Connected successfully.")

        # Command Sequence
        commands = [
            f"cd {project_root} && git pull origin main",
            f"cd {project_root} && sudo -S docker-compose pull",
            f"cd {project_root} && sudo -S docker-compose up -d",
            f"cd {project_root} && sudo -S docker-compose ps"
        ]

        for cmd in commands:
            print(f"> Running: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
            
            # Send password to sudo if prompt appears
            stdin.write(password + '\n')
            stdin.flush()
            
            # Print output in real-time
            for line in iter(stdout.readline, ""):
                print(line.strip())
            
            # Check for errors
            error = stderr.read().decode().strip()
            if error:
                print(f"Error output: {error}")

        ssh.close()
        print("\nDeployment sequence finished successfully.")
        
    except Exception as e:
        print(f"\nFATAL: Failed to connect or execute: {e}")
        sys.exit(1)

if __name__ == '__main__':
    deploy()
