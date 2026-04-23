import paramiko

def server_health_check():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Checking Server Resource Health...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Checking CPU, Memory and IO
        cmd = "top -b -n 1 | head -n 15 && free -m && df -h /"
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- SERVER RESOURCE SNAPSHOT ---")
        print(stdout.read().decode('utf-8'))
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    server_health_check()
