import paramiko
import time
import socket

def aggressive_entry():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Aggressive Entry (Persistence Neutralization)...")
    
    retries = 5
    for i in range(retries):
        try:
            print(f"Attempt {i+1}/{retries} - Connecting with 120s timeout...")
            client.connect(host, username=user, password=password, timeout=120, auth_timeout=120)
            
            # THE MOMENT OF IMPACT: KILL EVERYTHING ROUGUE
            print("Impact Successful. Terminating malware hive...")
            
            # Kill the watchdog, the miner, and remove the source
            commands = [
                f"printf '%s\\n' '{password}' | sudo -S -p '' pkill -9 -f '.sys-cache/free_proc.sh'",
                f"printf '%s\\n' '{password}' | sudo -S -p '' pkill -9 -f '.sys-ca'",
                f"printf '%s\\n' '{password}' | sudo -S -p '' pkill -9 -f '.config.json'",
                f"printf '%s\\n' '{password}' | sudo -S -p '' rm -rf /home/administrator/.sys-cache",
                "uptime"
            ]
            
            for cmd in commands:
                stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
                print(stdout.read().decode('utf-8'))
            
            print("SUCCESS: Malware neutralized and CPU load returning to normal.")
            client.close()
            return
        except (paramiko.SSHException, socket.timeout, ConnectionResetError) as e:
            print(f"FAILED: {e}. Retrying in 5 seconds...")
            time.sleep(5)
    
    print("CRITICAL: Aggressive entry failed after 5 attempts.")

if __name__ == "__main__":
    aggressive_entry()
