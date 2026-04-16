import paramiko

def debug_server():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=60, banner_timeout=200)
        
        # Fetch logs for 504 Error
        print("=== Recent Next.js Logs ===")
        command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker logs --tail 200 ongozacyberhub_django"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        with open('django_logs.txt', 'w', encoding='utf-8') as f:
            f.write(stdout.read().decode('utf-8', errors='ignore'))
            
        command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker logs --tail 200 ongozacyberhub_nextjs"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        with open('nextjs_logs.txt', 'w', encoding='utf-8') as f:
            f.write(stdout.read().decode('utf-8', errors='ignore'))
            
        print("Logs saved")
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    debug_server()
