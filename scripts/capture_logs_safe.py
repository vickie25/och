import paramiko

def capture_logs_to_file():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Capturing logs to server-side file...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Run for 15 seconds then kill, outputting to a file
        cmd = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' timeout 15s docker-compose -p hub_prod up django > /tmp/django_up.log 2>&1 || true"
        client.exec_command(cmd, get_pty=True)
        
        import time
        time.sleep(17) # Wait for timeout + buffer
        
        print("Reading log file...")
        # Use 'cat' which is safe
        cmd = "cat /tmp/django_up.log"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        
        # Read with errors='ignore' to be absolutely safe against encoding
        output = stdout.read().decode('utf-8', errors='ignore')
        print("\n--- PRODUCTION CRASH LOG ---")
        print(output)
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    capture_logs_to_file()
