import paramiko

def deploy():
    host = '69.30.235.220'
    port = 22
    username = 'administrator'
    password = 'Ongoza@#1'
    project_root = '/var/www/och'

    try:
        print(f"Connecting to {host} via SSH...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port, username, password, timeout=30)
        print("Connected.")

        commands = [
            f"cd {project_root} && sudo -S docker-compose restart nextjs"
        ]

        for cmd in commands:
            print(f"> Running: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
            stdin.write(password + '\n')
            stdin.flush()
            
            for line in iter(stdout.readline, ""):
                print(line.encode('utf-8', 'replace').decode('utf-8', 'replace').strip())

        ssh.close()
        print("Restarted nextjs.")
        
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == '__main__':
    deploy()
