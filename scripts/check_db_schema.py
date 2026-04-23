import os
import paramiko

def check_db_schema():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Use psql -c to avoid heredoc escaping issues
    cmd = 'docker exec hub_prod_django psql -U postgres -d ongozacyberhub -h 38.247.138.250 -c "\\\\d mfa_codes"'
    stdin, stdout, stderr = client.exec_command(cmd)
    print("--- mfa_codes ---")
    print(stdout.read().decode())
    
    cmd = 'docker exec hub_prod_django psql -U postgres -d ongozacyberhub -h 38.247.138.250 -c "\\\\d users"'
    stdin, stdout, stderr = client.exec_command(cmd)
    print("--- users ---")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_db_schema()
