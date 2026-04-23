import paramiko

def sniff_volumes():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Sniffing Docker volumes on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # List all volumes
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker volume ls --format '{{{{.Name}}}}'"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        
        print("\n--- FOUND VOLUMES ---")
        volumes = stdout.read().decode('utf-8', errors='ignore').splitlines()
        for vol in volumes:
            print(f"Volume: {vol.strip()}")
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    sniff_volumes()
