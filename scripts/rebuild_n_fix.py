import paramiko

def execute():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('69.30.235.220', username='administrator', password='Ongoza@#1', timeout=5)
        
        def run_sudo(cmd):
            stdin, stdout, stderr = c.exec_command(f'printf "Ongoza@#1\\n" | sudo -S -p "" {cmd}')
            return stdout.read().decode('utf-8').strip()
            
        print('--- Diagnosing and Rebuilding Next.js ---')
        print(run_sudo('cd /var/www/och && docker-compose build --no-cache nextjs && docker-compose up -d nextjs'))
        
        # Also let's fix the Django schema issue (BigInt/UUID conflicts) causing 500 error!
        print('--- Synchronizing Django Schema to prevent 500s ---')
        print(run_sudo('docker exec hub_prod_django python manage.py migrate --fake-initial'))
        print(run_sudo('docker exec hub_prod_django python manage.py migrate'))
        
    except Exception as e:
        print('Failed:', e)

if __name__ == '__main__':
    execute()
