import paramiko

def crypto_cleanup():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Emergency Security Cleanup...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Kill the rogue processes found (734745, 3153208)
        # Using -9 to force kill malware threads
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' kill -9 734745 3153208 2>/dev/null || echo 'PIDs not found, searching for others...'"
        client.exec_command(cmd, get_pty=True)

        # 2. Kill by name (in case PIDs changed)
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' pkill -f '.sys-ca' && sudo -S -p '' pkill -f '.config.json'"
        client.exec_command(cmd, get_pty=True)
        
        # 3. Secure the home directory
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' rm -rf /home/administrator/.sys-ca /home/administrator/.config.json /tmp/.sys-ca"
        client.exec_command(cmd, get_pty=True)

        # 4. Final verify of CPU
        cmd = "top -b -n 1 | head -n 15"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- POST-CLEANUP CPU STATUS ---")
        print(stdout.read().decode('utf-8'))

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    crypto_cleanup()
