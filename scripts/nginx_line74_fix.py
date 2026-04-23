import paramiko

def nginx_line74_fix():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print("Executing Surgical Nginx Fix on Line 74...")
    try:
        client.connect(host, username=user, password=password, timeout=120)
        
        def run_sudo(cmd):
            stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}", get_pty=True)
            return stdout.read().decode('ascii', 'ignore').strip()

        # Get current config
        conf_file = "/etc/nginx/conf.d/default.conf"
        content = run_sudo(f"docker exec hub_prod_nginx cat {conf_file}")
        
        # Show line 74 context
        lines = content.split('\n')
        print("\n--- CONTEXT AROUND LINE 74 ---")
        for i, line in enumerate(lines):
            if 65 <= (i+1) <= 85:
                print(f"{i+1}: {line}")

        # Fix all references to 'django' that are causing DNS failures
        # This is a nuclear replace for 'django' where followed by ':' or '/' or ';'
        fixed_content = content.replace("http://django:8000", "http://hub_prod_django:8000")
        fixed_content = fixed_content.replace("http://django;", "http://hub_prod_django:8000;")
        fixed_content = fixed_content.replace("upstream django", "upstream hub_prod_django")
        fixed_content = fixed_content.replace("proxy_pass http://django", "proxy_pass http://hub_prod_django:8000")
        
        # Also fix any standalone 'django' references in upstream blocks
        # Nginx error was: "host not found in upstream 'django'"
        # This usually means 'server django:8000;' inside a block.
        fixed_content = fixed_content.replace("server django:8000", "server hub_prod_django:8000")

        # Write to temp and copy
        write_cmd = f"cat << 'EOF' > /tmp/nginx_surgery.conf\n{fixed_content}\nEOF"
        client.exec_command(write_cmd)
        run_sudo(f"docker cp /tmp/nginx_surgery.conf hub_prod_nginx:{conf_file}")
        
        # Test and Reload
        print("\n--- Testing and Reloading ---")
        test_res = run_sudo("docker exec hub_prod_nginx nginx -t")
        print(f"Nginx Test:\n{test_res}")
        
        if "test is successful" in test_res:
            run_sudo("docker exec hub_prod_nginx nginx -s reload")
            print("Nginx Reloaded Successfully!")
        else:
            print("ERROR: Precision fix failed. Manual intervention needed on contents below.")

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    nginx_line74_fix()
