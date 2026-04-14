import paramiko

def check_all_containers():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("=== Complete Container Status List ===")
        command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker ps -a --format '{{{{.Names}}}}\\t{{{{.Status}}}}'"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_all_containers()
