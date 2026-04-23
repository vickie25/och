import paramiko

def sniff_upstream():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Sniffing upstream connectivity on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Check Nginx error logs for upstream failures
        print("\n--- NGINX ERRORS ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker logs hub_prod_nginx --tail 20"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        # Check if Django is actually listening
        print("\n--- DJANGO STATUS ---")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_django netstat -tulpn 2>/dev/null || echo 'netstat not found'"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    sniff_upstream()
