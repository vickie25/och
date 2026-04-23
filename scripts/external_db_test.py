import paramiko
import time

def external_db_test():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    # Credentials provided by user
    ext_db_host = "138.197.203.235"
    ext_db_name = "ongozacyberhub"
    ext_db_user = "ongoza_user"
    ext_db_pass = "ongoza3485cyber758hub434"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Testing connection to External Database at {ext_db_host}...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Try to ping the host
        cmd = f"ping -c 3 {ext_db_host}"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print("\n--- PING TEST ---")
        print(stdout.read().decode('utf-8'))

        # 2. Try to connect via psql from the server
        print("\n--- PSQL CONNECTION TEST ---")
        cmd = f"PGPASSWORD='{ext_db_pass}' psql -h {ext_db_host} -U {ext_db_user} -d {ext_db_name} -c 'SELECT count(*) FROM users_user;' 2>&1"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        result = stdout.read().decode('utf-8').strip()
        print(result)

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    external_db_test()
