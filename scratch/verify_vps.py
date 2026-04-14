import paramiko

def check_vps_status():
    host = '69.30.235.220'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, 22, 'administrator', 'Ongoza@#1')
    
    # 1. Image ID
    stdin, stdout, stderr = ssh.exec_command('docker inspect ghcr.io/cresdynamics-lang/och-nextjs:latest --format "{{.Id}}"')
    image_id = stdout.read().decode('utf-8').strip()
    print(f"Next.js Image ID: {image_id}")
    
    # 2. Container Name and Image ID in use
    stdin, stdout, stderr = ssh.exec_command('docker ps --filter "name=nextjs" --format "{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"')
    print(f"Running Containers:\n{stdout.read().decode('utf-8')}")
    
    # 3. Last 10 lines of logs to confirm start
    stdin, stdout, stderr = ssh.exec_command('docker logs --tail 10 ongozacyberhub_nextjs')
    print(f"Logs:\n{stdout.read().decode('utf-8')}")
    
    ssh.close()

if __name__ == '__main__':
    check_vps_status()
