import paramiko

def execute():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('69.30.235.220', username='administrator', password='Ongoza@#1', timeout=5)
        
        def run_sudo(cmd):
            stdin, stdout, stderr = c.exec_command(f'printf "Ongoza@#1\\n" | sudo -S -p "" {cmd}')
            return stdout.read().decode('utf-8').strip()
            
        print('--- checking nextjs_app envs ---')
        print(run_sudo('ls -la /var/www/och/frontend/nextjs_app/ | grep env'))
        print(run_sudo('cat /var/www/och/frontend/nextjs_app/.env'))
        print('--- checking docker-compose volume mapping ---')
        print(run_sudo('grep -A 5 "env_file" /var/www/och/docker-compose.yml'))
        
    except Exception as e:
        print('Failed:', e)

if __name__ == '__main__':
    execute()
