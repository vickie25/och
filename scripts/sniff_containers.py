import paramiko

def sniff_containers():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Sniffing container names on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=20)
        
        command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker ps -a --format '{{{{.Names}}}}'"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        names = stdout.read().decode().splitlines()
        
        print("\n--- FOUND CONTAINERS ---")
        for name in names:
            if name.strip():
                print(f"Container: {name.strip()}")
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    sniff_containers()
