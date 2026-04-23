import paramiko
import re

def update_db_env():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"

    print("Connecting to host to update Django .env DB credentials...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=60)
        
        def run_sudo(cmd):
            stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}")
            return stdout.read().decode('utf-8', 'ignore').strip()

        env_path = "/var/www/och/backend/django_app/.env"
        
        # Read current .env
        content = run_sudo(f"cat {env_path}")
        
        # Replace the POSTGRES variables
        new_content = re.sub(r'POSTGRES_USER=.*', 'POSTGRES_USER=ongoza_user', content)
        new_content = re.sub(r'POSTGRES_PASSWORD=.*', 'POSTGRES_PASSWORD=ongoza3485cyber758hub434', new_content)
        new_content = re.sub(r'POSTGRES_HOST=.*', 'POSTGRES_HOST=138.197.203.235', new_content)
        
        if new_content != content:
            print(f"Patching {env_path}...")
            escaped_content = new_content.replace("\\", "\\\\").replace("$", "\\$").replace("`", "\\`")
            write_cmd = f'cat << \'EOF\' > /tmp/env_patch.conf\n{new_content}\nEOF'
            client.exec_command(write_cmd)
            run_sudo(f"cp /tmp/env_patch.conf {env_path}")
            
            # Restart Django
            print("\nRestarting Django container to apply DB changes...")
            run_sudo("cd /var/www/och && docker-compose restart django")
            
            # Wait a few seconds for Django to come up
            run_sudo("sleep 10")
            
            # Print Django logs
            print("\nDjango Logs:")
            print(run_sudo("docker logs --tail 20 hub_prod_django"))
        else:
            print(f"No changes needed for {env_path}")
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_db_env()
