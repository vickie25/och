import paramiko
import time

def refresh_server():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("=== Restarting Containers for Fresh Code Load ===")
        command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose restart django nextjs fastapi"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        print("\n=== Verifying Fresh Uptime ===")
        time.sleep(5)
        command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker ps --format 'table {{.Names}}\\t{{.Status}}'"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    refresh_server()
