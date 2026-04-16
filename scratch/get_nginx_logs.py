import paramiko

def get_nginx_logs():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("=== Nginx Error Logs ===")
        # Check specifically for error log
        command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec ongozacyberhub_nginx tail -n 50 /var/log/nginx/error.log"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        print("\n=== Nginx Access Logs (Recent) ===")
        command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker logs ongozacyberhub_nginx --tail 20"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    get_nginx_logs()
