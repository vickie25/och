import os
import paramiko

def run_sql():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        cmd = f'printf "%s\\n" "{password}" | sudo -S docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c "UPDATE user_roles SET is_active=true RETURNING *;"'
        
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', 'ignore')
        
        print("=== OUT ===")
        print(out)
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_sql()
