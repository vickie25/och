import paramiko
import sys
import time

def deploy():
    host = '69.30.235.220'
    port = 22
    username = 'administrator'
    password = 'Ongoza@#1'

    try:
        print("Connecting to server...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port, username, password, timeout=30)
        print("Connected successfully.")

        # Let's run the build step by step sequentially to completely avoid memory spikes
        commands = [
            "cd /var/www/och && git pull origin main",
            "sudo docker builder prune -a -f",
            "cd /var/www/och && sudo DOCKER_BUILDKIT=0 docker-compose build nextjs",
            "cd /var/www/och && sudo DOCKER_BUILDKIT=0 docker-compose build",
            "cd /var/www/och && sudo docker-compose up -d",
        ]

        for cmd in commands:
            print(f"> Running: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
            stdin.write(password + '\n')
            stdin.flush()
            
            while True:
                line = stdout.readline()
                if not line:
                    break
                print(line.strip())
            
            err = stderr.read().decode().strip()
            if err:
                print(f"Error output: {err}")

        ssh.close()
        print("Deployment sequence finished.")
    except Exception as e:
        print(f"Failed to connect or execute: {e}")

if __name__ == '__main__':
    deploy()
