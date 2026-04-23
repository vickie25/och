import paramiko

def nginx_django_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(host, username=user, password=password, timeout=120)
        print("Connected.\n")

        def run_sudo(cmd):
            stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}", get_pty=True)
            return stdout.read().decode('ascii', 'ignore').strip()

        # 1. Inspect Nginx configuration
        print("=== STEP 1: NGINX CONFIGURATION ===")
        # Find the nginx config file
        nginx_conf_path = run_sudo("docker exec hub_prod_nginx find /etc/nginx -name 'default.conf' -o -name 'nginx.conf'")
        print(f"Conf paths found:\n{nginx_conf_path}")
        
        for path in nginx_conf_path.split('\n'):
            if path:
                print(f"\n--- {path} ---")
                print(run_sudo(f"docker exec hub_prod_nginx cat {path}"))

        # 2. Check internal connectivity from Nginx to Django
        print("\n=== STEP 2: INTERNAL CONNECTIVITY TEST ===")
        # Test if Nginx container can reach 'django' on port 8000
        conn_test = run_sudo("docker exec hub_prod_nginx curl -I http://django:8000/ 2>&1")
        print(f"Nginx -> Django (port 8000): {conn_test}")

        # 3. Check Django's running process inside the container
        print("\n=== STEP 3: DJANGO PROCESS AUDIT ===")
        print(run_sudo("docker exec hub_prod_django ps aux"))
        print("\n--- Listening Ports in Django Container ---")
        print(run_sudo("docker exec hub_prod_django netstat -tlnp || docker exec hub_prod_django ss -tlnp || echo 'Netstat/ss not found'"))

        # 4. Check ALLOWED_HOSTS
        print("\n=== STEP 4: DJANGO ALLOWED_HOSTS ===")
        print(run_sudo("docker exec hub_prod_django env | grep ALLOWED_HOSTS"))
        print(run_sudo("cat /var/www/och/backend/django_app/.env | grep ALLOWED_HOSTS"))

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    nginx_django_audit()
