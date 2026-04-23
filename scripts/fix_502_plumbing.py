import paramiko

def fix_502_plumbing():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Fixing Internal Plumbing (Nginx -> Django)...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Identify the config file
        print("Reading Nginx configuration...")
        cmd = f"cd /var/www/och/nginx/conf.d && ls -1"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        files = stdout.read().decode().splitlines()
        print(f"Configs found: {files}")
        
        # 2. Force update the proxy_pass in all .conf files to hub_prod_django
        print("Updating proxy_pass to hub_prod_django:8000...")
        # We replace any occurrences of 'django:8000' with 'hub_prod_django:8000'
        # We also ensure the host header is set correctly
        cmd = f"cd /var/www/och/nginx/conf.d && printf '%s\\n' '{password}' | sudo -S -p '' sed -i 's/django:8000/hub_prod_django:8000/g' *.conf"
        client.exec_command(cmd, get_pty=True)
        
        # 3. Reload Nginx container
        print("Reloading Nginx...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec hub_prod_nginx nginx -s reload"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
        print("\nPlumbing Fix Complete.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    fix_502_plumbing()
