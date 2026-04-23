import paramiko

def execute():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('69.30.235.220', username='administrator', password='Ongoza@#1', timeout=5)
        
        def run_sudo(cmd):
            stdin, stdout, stderr = c.exec_command(f'printf "Ongoza@#1\\n" | sudo -S -p "" {cmd}')
            return stdout.read().decode('utf-8').strip()
            
        print('--- Django Error Traceback ---')
        # Get logs safely, using a python loop instead of bash grep to avoid quoting issues
        command = "docker logs --tail 300 hub_prod_django"
        logs = run_sudo(command)
        
        lines = logs.split('\\n')
        capture = False
        for line in lines:
            if 'Traceback' in line or '500' in line or 'ProgrammingError' in line or 'relation' in line:
                print(line)
        
    except Exception as e:
        print('Failed:', e)

if __name__ == '__main__':
    execute()
