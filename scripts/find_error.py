import paramiko
try:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('69.30.235.220', username='administrator', password='Ongoza@#1', timeout=5)
    
    def run_sudo(cmd):
        stdin, stdout, stderr = c.exec_command(f'printf "Ongoza@#1\\n" | sudo -S -p "" {cmd}')
        return stdout.read().decode('utf-8').strip(), stderr.read().decode('utf-8').strip()
        
    out, err = run_sudo('grep -rn "Something went wrong" /var/www/och/backend/django_app/')
    print(out)
except Exception as e:
    print('Failed:', e)
