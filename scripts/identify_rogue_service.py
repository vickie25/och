import paramiko

def identify_rogue_service():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Identifying the Rogue 300% CPU Service...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # PIDs found in last check: 734745, 3153208
        cmd = "ps -p 734745,3153208 -o comm,args,unit"
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- ROGUE SERVICE DETAILS ---")
        print(stdout.read().decode('utf-8'))
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    identify_rogue_service()
