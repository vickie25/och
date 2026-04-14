import paramiko

def check_final():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Full Container Status (No truncation)
        print("=== Full Container Status ===")
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose ps -a"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        # 2. .env File Verification
        print("\n=== .env File Verification ===")
        command = "ls -la /var/www/och/backend/django_app/.env"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        # 3. Virtual/Hidden Resource Autopsy
        print("\n=== Virtual Resource Audit (.next/standalone and hidden) ===")
        command = "ls -la /var/www/och/frontend/nextjs_app/.next/standalone 2>/dev/null && ls -la /var/www/och/frontend/nextjs_app/node_modules/.bin/next"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_final()
