import paramiko

def execute():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('69.30.235.220', username='administrator', password='Ongoza@#1', timeout=5)
        
        def run_sudo(cmd):
            stdin, stdout, stderr = c.exec_command(f'printf "Ongoza@#1\\n" | sudo -S -p "" {cmd}')
            return stdout.read().decode('utf-8').strip()
            
        print('--- Checking Docker Container States ---')
        print(run_sudo('docker ps -a --format "{{.Names}} - {{.Status}}" | grep -E "django|nextjs|postgres"'))
        
        # Also check django logs to see why it crashed if it did
        print('\n--- Django Logs Tail ---')
        print(run_sudo('docker logs --tail 20 hub_prod_django'))
        
    except Exception as e:
        print('Failed:', e)

if __name__ == '__main__':
    execute()
