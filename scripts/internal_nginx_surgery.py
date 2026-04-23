import paramiko

def internal_nginx_surgery():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Internal Nginx Surgery (Final Fix)...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Update the plumbing INSIDE the container to ensure we hit the right files
        print("Surgically updating internal Nginx configs...")
        # We replace any occurrences of 'django' with 'hub_prod_django' across all conf files
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_nginx sh -c \"sed -i 's/django:8000/hub_prod_django:8000/g' /etc/nginx/conf.d/*.conf 2>/dev/null || true\""
        client.exec_command(cmd, get_pty=True)
        
        # 2. Also check for a common 'upstream' block in nginx.conf if it exists
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_nginx sh -c \"sed -i 's/django:8000/hub_prod_django:8000/g' /etc/nginx/nginx.conf 2>/dev/null || true\""
        client.exec_command(cmd, get_pty=True)

        # 3. Last stand: try to reload Nginx
        print("Final Reload...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_nginx nginx -s reload"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
        print("\nSurgery Complete. Checking site...")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    internal_nginx_surgery()
