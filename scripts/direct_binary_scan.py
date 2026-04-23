import paramiko

def direct_binary_scan():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Direct Binary Scan for 55 Users...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # We'll use 'strings' to find printable characters in the binary files
        # Searching for the '@' symbol which is common in emails
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v och_postgres_data:/data alpine strings -n 10 /data/base/16384/16387 | grep '@' | head -n 10"
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- DETECTED EMAILS IN RAW BYTES ---")
        # Reading raw to avoid decode error, then doing a safe conversion
        raw_output = stdout.read()
        print(raw_output.decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    direct_binary_scan()
