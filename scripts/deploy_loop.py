import paramiko
import time
import sys

def run_deployment():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    max_attempts = 10
    attempt = 1
    success = False
    
    while not success and attempt <= max_attempts:
        print(f"=== Deployment Attempt {attempt} of {max_attempts} ===")
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, username=user, password=password)
            
            # The full deployment command
            commands = [
                "cd /var/www/och",
                "git pull origin main",
                f"printf '%s\\n' '{password}' | sudo -S -p '' docker-compose up -d --build",
                f"printf '%s\\n' '{password}' | sudo -S -p '' docker-compose ps"
            ]
            
            full_command = " && ".join(commands)
            print(f"Executing deployment command on {host}...")
            
            stdin, stdout, stderr = client.exec_command(full_command, get_pty=True)
            
            # Monitor output in real-time
            oom_detected = False
            for line in iter(stdout.readline, ""):
                print(line, end="")
                if "SIGKILL" in line or "exit code: 1" in line:
                    oom_detected = True
            
            # Check final status
            if oom_detected:
                print("\n[!] Build failed (possibly OOM). Cleaning cache and retrying...")
                client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' docker-compose down", get_pty=True)
                time.sleep(15)
            else:
                # Verify health
                print("\nChecking container health...")
                stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' docker-compose ps", get_pty=True)
                ps_output = stdout.read().decode()
                print(ps_output)
                
                if "Up" in ps_output or "healthy" in ps_output:
                    print("\n[✓] DEPLOYMENT SUCCESSFUL AND VERIFIED")
                    success = True
                else:
                    print("\n[-] Containers not ready yet. Waiting...")
                    time.sleep(10)
            
            client.close()
            
        except Exception as e:
            print(f"\n[!] SSH Error: {str(e)}")
            time.sleep(10)
        
        attempt += 1

    if not success:
        print("\n[!!!] DEPLOYMENT FAILED AFTER ALL ATTEMPTS")
        sys.exit(1)

if __name__ == "__main__":
    run_deployment()
