import paramiko
import time

host = "69.30.235.220"
ssh_user = "administrator"
password = "Ongoza@#1"

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=ssh_user, password=password)

    transport = client.get_transport()

    ch = transport.open_session()
    ch.get_pty()
    
    cmd = (
        f"printf '%s\\n' '{password}' | sudo -S -p '' bash -c '"
        f"cd /var/www/och && git pull origin main && "
        f"docker-compose build nextjs > build.log 2>&1 && "
        f"docker-compose up -d nextjs'"
    )
    ch.exec_command(cmd)
    
    print("Deployment started in background on server. Check build.log if needed.")
    
    # Wait for the command to finish up to 120 secs
    for _ in range(120):
        if ch.exit_status_ready():
            break
        time.sleep(1)
        
    status = ch.recv_exit_status() if ch.exit_status_ready() else "TIMEOUT"
    print(f"Deployment script finished with status: {status}")
    
    client.close()
except Exception as e:
    print(f"Error: {e}")
