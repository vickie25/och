import paramiko

def network_alignment():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print("Executing Network Alignment Diagnostic...")
    try:
        client.connect(host, username=user, password=password, timeout=120)
        
        def run_sudo(cmd):
            stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}", get_pty=True)
            return stdout.read().decode('ascii', 'ignore').strip()

        # 1. Inspect Docker Networks
        print("\n--- DOCKER NETWORKS ---")
        print(run_sudo("docker network ls"))
        
        # 2. Inspect Nginx and Django containers
        print("\n--- NGINX NETWORK DETAILS ---")
        print(run_sudo("docker inspect hub_prod_nginx --format '{{json .NetworkSettings.Networks}}'"))
        
        print("\n--- DJANGO NETWORK DETAILS ---")
        print(run_sudo("docker inspect hub_prod_django --format '{{json .NetworkSettings.Networks}}'"))

        # 3. Test resolution using container name instead of service name
        print("\n--- RESOLUTION TEST (hub_prod_django) ---")
        res_test = run_sudo("docker exec hub_prod_nginx getent hosts hub_prod_django || echo 'Failed to resolve'")
        print(f"Resolve hub_prod_django: {res_test}")
        
        # 4. Test connectivity to port 8000 on the container IP directly
        django_ip = run_sudo("docker inspect hub_prod_django --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'")
        print(f"Django Container IP: {django_ip}")
        
        if django_ip:
            conn_test = run_sudo(f"docker exec hub_prod_nginx curl -I http://{django_ip}:8000/ 2>&1")
            print(f"Nginx -> Django IP ({django_ip}:8000): {conn_test}")

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    network_alignment()
