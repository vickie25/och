import paramiko

def forced_capture_logs():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Capturing live build/crash logs on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # We run 'up' without -d for a few seconds then stop to capture stdout/stderr
        # We use a timeout on the command itself
        print("Starting Django in non-detached mode (30s capture)...")
        cmd = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' timeout 30s docker-compose -p hub_prod up django"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        
        output = stdout.read().decode()
        print("\n--- CAPTURED OUTPUT ---")
        print(output)
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    forced_capture_logs()
