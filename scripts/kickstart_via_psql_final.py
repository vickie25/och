import os
import paramiko
import sys

def kickstart_via_psql_final():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # 1. Direct psql INSERT with manual COMMIT just in case
        print("\n--- [STEP 1: PSQL INSERT] ---")
        sql = "INSERT INTO django_migrations (app, name, applied) VALUES ('users', '0001_initial', '2026-04-10 00:00:00+00');"
        command = f"sudo docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"{sql}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 2. Direct psql VERIFY
        print("\n--- [STEP 2: PSQL VERIFY] ---")
        sql = "SELECT app, name, applied FROM django_migrations WHERE app='users';"
        command = f"sudo docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"{sql}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    kickstart_via_psql_final()
