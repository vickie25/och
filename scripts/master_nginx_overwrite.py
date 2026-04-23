import paramiko

def master_nginx_overwrite():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print("Executing Master Nginx Overwrite...")
    try:
        client.connect(host, username=user, password=password, timeout=120)
        
        def run_sudo(cmd):
            stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}", get_pty=True)
            return stdout.read().decode('ascii', 'ignore').strip()

        # 1. Read the WHOLE default.conf
        conf_file = "/etc/nginx/conf.d/default.conf"
        print(f"\n--- FULL CONTENT OF {conf_file} ---")
        content = run_sudo(f"docker exec hub_prod_nginx cat {conf_file}")
        print(content)

        # 2. Patch logic - for now, just print it so I can see it.
        # But let's apply the fix we know is needed.
        django_ip = "172.19.0.2" # Known from previous step
        
        fixed_content = content.replace("django:8000", f"{django_ip}:8000")
        fixed_content = fixed_content.replace("http://django", f"http://{django_ip}")
        fixed_content = fixed_content.replace("upstream django", f"upstream {django_ip}")
        
        if content != fixed_content:
            print("\n--- Applying Fix to Host ---")
            write_cmd = f"cat << 'EOF' > /tmp/master_nginx.conf\n{fixed_content}\nEOF"
            client.exec_command(write_cmd)
            run_sudo(f"docker cp /tmp/master_nginx.conf hub_prod_nginx:{conf_file}")
            
            # 3. Test and Reload
            test_res = run_sudo("docker exec hub_prod_nginx nginx -t")
            print(f"Nginx Test:\n{test_res}")
            
            if "test is successful" in test_res:
                run_sudo("docker exec hub_prod_nginx nginx -s reload")
                print("Nginx Reloaded Successfully!")
        else:
            print("No differences found in replace attempt.")

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    master_nginx_overwrite()
