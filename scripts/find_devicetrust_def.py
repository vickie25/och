import paramiko

def execute():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('69.30.235.220', username='administrator', password='Ongoza@#1', timeout=5)
        
        def run_sudo(cmd):
            stdin, stdout, stderr = c.exec_command(f'printf "Ongoza@#1\\n" | sudo -S -p "" {cmd}')
            return stdout.read().decode('utf-8').strip(), stderr.read().decode('utf-8').strip()
            
        out, _ = run_sudo("cat /var/www/och/backend/django_app/users/models.py | grep -i 'class DeviceTrust'")
        print("Class DeviceTrust def:\\n", out)
        
        # If not in models.py, let's look for DeviceTrust in the whole users app
        out, _ = run_sudo("cd /var/www/och/backend/django_app/users && grep -rn 'class DeviceTrust'")
        print("DeviceTrust anywhere in users:\\n", out)
        
    except Exception as e:
        print('Failed:', e)

if __name__ == '__main__':
    execute()
