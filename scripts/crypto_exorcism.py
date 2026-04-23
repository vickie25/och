import paramiko

def crypto_exorcism():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Permanent Crypto-Malware Exorcism...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Kill the Watchdog parent process
        print("Killing the Watchdog parent (PID 3153209)...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' kill -9 3153209 2>/dev/null || echo 'Watchdog PID not found, already killed?'"
        client.exec_command(cmd, get_pty=True)

        # 2. Kill all processes matching sys-ca and config.json
        print("Terminating all rogue miner threads...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' pkill -f '.sys-ca' && sudo -S -p '' pkill -f '.config.json'"
        client.exec_command(cmd, get_pty=True)
        
        # 3. Terminate the rogue systemd masquerade find last check: 769262
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' kill -9 769262 2>/dev/null"
        client.exec_command(cmd, get_pty=True)

        # 4. Burn the Malware folder (the source hive)
        print("Deleting the hidden malware directory (.sys-cache)...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' rm -rf /home/administrator/.sys-cache"
        client.exec_command(cmd, get_pty=True)

        # 5. Final Verify
        cmd = "top -b -n 1 | head -n 15"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- FINAL CPU RECOVERY STATUS ---")
        print(stdout.read().decode('utf-8'))

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    crypto_exorcism()
