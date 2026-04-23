import paramiko

def nginx_manual_read():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print("Executing Manual Nginx Config Surgery...")
    try:
        client.connect(host, username=user, password=password, timeout=120)
        
        def run_sudo(cmd):
            stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}", get_pty=True)
            return stdout.read().decode('ascii', 'ignore').strip()

        # Read default.conf with line numbers
        print("\n--- DEFAULT.CONF (Lines 60-90) ---")
        print(run_sudo("docker exec hub_prod_nginx cat -n /etc/nginx/conf.d/default.conf | sed -n '60,90p'"))

        # Read ssl.conf too just in case
        print("\n--- SSL.CONF (Lines 1-30) ---")
        print(run_sudo("docker exec hub_prod_nginx cat -n /etc/nginx/conf.d/ssl.conf | head -30"))

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    nginx_manual_read()
