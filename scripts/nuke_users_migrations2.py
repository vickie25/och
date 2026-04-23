import paramiko

def execute():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('69.30.235.220', username='administrator', password='Ongoza@#1', timeout=5)
        
        def run_sudo(cmd):
            stdin, stdout, stderr = c.exec_command(f'printf "Ongoza@#1\\n" | sudo -S -p "" {cmd}')
            return stdout.read().decode('utf-8').strip(), stderr.read().decode('utf-8').strip()
            
        print("Checking showmigrations ... ")
        out, _ = run_sudo("docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c \\"SELECT * FROM django_migrations WHERE app='users';\\"")
        print(out)
        
        print("Deleting users from django_migrations to force table creation...")
        sql = "DELETE FROM django_migrations WHERE app='users';"
        run_sudo(f"docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c \\"{sql}\\"")
        
        print("Re-running migrate for users app...")
        out, err = run_sudo("docker exec hub_prod_django python manage.py migrate users")
        print(out)
        if err: print("Migrate Err:", err)
        
        print("Checking if users_devicetrust exists now...")
        out, _ = run_sudo("docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c '\\dt users_*'")
        print(out)
        
    except Exception as e:
        print('Failed:', e)

if __name__ == '__main__':
    execute()
