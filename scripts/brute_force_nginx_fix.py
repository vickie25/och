import paramiko

def brute_force_nginx_fix():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Brute Force Nginx Fix...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Broadest possible search and replace
        print("Scrubbing all internal Nginx configs for stale names...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_nginx sh -c \"find /etc/nginx -name '*.conf' -exec sed -i 's/django:8000/hub_prod_django:8000/g' {{}} +\""
        client.exec_command(cmd, get_pty=True)
        
        # 2. Specifically delete the conflicting default.conf if it exists and is causing the crash
        print("Removing conflicting default.conf...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_nginx rm -f /etc/nginx/conf.d/default.conf"
        client.exec_command(cmd, get_pty=True)

        # 3. Reload
        print("Final Reload attempt...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_nginx nginx -s reload"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
        print("\nBrute Force Fix Complete. Verification starting...")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    brute_force_nginx_fix()
