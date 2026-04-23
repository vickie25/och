import paramiko

def nginx_error_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Auditing Nginx Error Logs (Analysis Only)...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Reading the last 20 Nginx error logs
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_nginx tail -n 20 /var/log/nginx/error.log"
        
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- NGINX ERROR LOGS ---")
        print(stdout.read().decode('utf-8'))
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    nginx_error_audit()
