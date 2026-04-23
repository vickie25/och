import paramiko

host = "69.30.235.220"
user = "administrator"
password = "Ongoza@#1"

try:
    print("Connecting to host to add missing /admin/ location to Nginx...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=60)
    
    def run_sudo(cmd):
        stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}")
        return stdout.read().decode('utf-8', 'ignore').strip()

    conf_path = "/var/www/och/nginx/conf.d-local/default.conf"
    
    # Read the file
    content = run_sudo(f"cat {conf_path}")
    
    # Inject the admin block just before the end of the first server block handling port 443
    # Wait, simple string manipulation: look for location /api/ and insert it there.
    
    admin_block = """
    # Backend Admin (Django)
    location /admin {
        proxy_pass http://hub_prod_django:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $forwarded_proto;
    }
    """
    
    if "location /api/" in content:
        new_content = content.replace("location /api/", admin_block + "\n    location /api/")
        
        # Write back
        escaped = new_content.replace("\\", "\\\\").replace("$", "\\$").replace("`", "\\`")
        write_cmd = f'cat << \'EOF\' > /tmp/admin_patch.conf\n{new_content}\nEOF'
        client.exec_command(write_cmd)
        run_sudo(f"cp /tmp/admin_patch.conf {conf_path}")
        run_sudo(f"chmod 644 {conf_path}")
        
        # Reload
        test_out = run_sudo("docker exec hub_prod_nginx nginx -t 2>&1")
        if "syntax is ok" in test_out.lower() or "test is successful" in test_out.lower():
            print("Reloading Nginx...")
            run_sudo("docker exec hub_prod_nginx nginx -s reload")
            print("Done. Admin is now mapped!")
        else:
            print("Nginx Test failed: " + test_out)
    else:
        print("Couldn't find location /api/ to anchor the replacement.")
        
    client.close()
except Exception as e:
    print(f"Error: {e}")
