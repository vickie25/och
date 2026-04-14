import paramiko

def check_db_health():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("=== PostgreSQL Logs (Last 20 lines) ===")
        command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker logs ongozacyberhub_postgres --tail 20"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        print("\n=== Active Container List ===")
        command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker ps --format 'table {{.Names}}\\t{{.Status}}'"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_db_health()
