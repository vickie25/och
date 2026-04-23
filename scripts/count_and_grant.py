import paramiko

def count_and_grant():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(host, username=user, password=password, timeout=120, auth_timeout=120, banner_timeout=120)
        print("Connected.\n")

        # Kill malware again
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' pkill -9 -f '.sys-ca' 2>/dev/null; printf '%s\\n' '{password}' | sudo -S -p '' pkill -9 -f 'free_proc' 2>/dev/null; printf '%s\\n' '{password}' | sudo -S -p '' rm -rf /home/administrator/.sys-cache 2>/dev/null"
        client.exec_command(cmd, get_pty=True)

        container = "hub_prod_postgres"

        # 1. Count users in the postgres database
        print("=== USER COUNT (postgres database, users table) ===")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec {container} psql -U postgres -d postgres -t -c 'SELECT count(*) FROM users;'"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        count = stdout.read().decode('utf-8', 'ignore').strip()
        print(f"Total users: {count}")

        # 2. Show a few user emails to confirm
        print("\n=== SAMPLE USERS (first 10) ===")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec {container} psql -U postgres -d postgres -t -c \"SELECT email, first_name, last_name, is_active FROM users LIMIT 10;\""
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        # 3. Check if cresdynamics@gmail.com exists
        print("\n=== CHECKING cresdynamics@gmail.com ===")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec {container} psql -U postgres -d postgres -t -c \"SELECT id, email, first_name, is_staff, is_superuser FROM users WHERE email = 'cresdynamics@gmail.com';\""
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        result = stdout.read().decode('utf-8', 'ignore').strip()
        print(result if result else "Not found in database")

        # 4. Check which database Django is ACTUALLY using by checking the ongozacyberhub db too
        print("\n=== USER COUNT (ongozacyberhub database) ===")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec {container} psql -U postgres -d ongozacyberhub -t -c 'SELECT count(*) FROM users;' 2>&1"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore').strip())

        # 5. Check the django_migrations table to understand which db Django manages
        print("\n=== DJANGO MIGRATIONS COUNT ===")
        print("In postgres db:")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec {container} psql -U postgres -d postgres -t -c 'SELECT count(*) FROM django_migrations;' 2>&1"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore').strip())

        print("In ongozacyberhub db:")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec {container} psql -U postgres -d ongozacyberhub -t -c 'SELECT count(*) FROM django_migrations;' 2>&1"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore').strip())

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    count_and_grant()
