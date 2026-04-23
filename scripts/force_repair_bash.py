import os
import paramiko
import sys

def force_repair_bash():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Create a bash script on the server that does everything in one go
        bash_script = """
set -e
echo "Inserting migration record..."
sudo docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c "INSERT INTO django_migrations (app, name, applied) VALUES ('users', '0001_initial', '2026-04-10 00:00:00+00') ON CONFLICT (app, name) DO NOTHING;"
sudo docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c "INSERT INTO django_migrations (app, name, applied) VALUES ('organizations', '0001_initial', '2026-04-10 00:00:00+00') ON CONFLICT (app, name) DO NOTHING;"

echo "Verifying..."
sudo docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c "SELECT * FROM django_migrations WHERE app='users';"

# IF VERIFIED, proceed to migrate
echo "Running migrate..."
sudo docker exec hub_prod_django python manage.py migrate
"""
        # Upload and run
        client.exec_command(f"echo '{bash_script}' > /tmp/repair.sh")
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" bash /tmp/repair.sh', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    force_repair_bash()
