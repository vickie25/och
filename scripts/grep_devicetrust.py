import paramiko

def execute():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('69.30.235.220', username='administrator', password='Ongoza@#1', timeout=5)
        
        def run_sudo(cmd):
            stdin, stdout, stderr = c.exec_command(f'printf "Ongoza@#1\\n" | sudo -S -p "" {cmd}')
            return stdout.read().decode('utf-8').strip(), stderr.read().decode('utf-8').strip()
            
        out, _ = run_sudo("grep -rn 'DeviceTrust' /var/www/och/backend/django_app/")
        print("DeviceTrust References:\\n", out)
        
    except Exception as e:
        print('Failed:', e)

if __name__ == '__main__':
    execute()
