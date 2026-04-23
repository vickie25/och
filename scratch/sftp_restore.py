import paramiko
import os

def sftp_restore():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    local_path = "docker-compose.yml"
    remote_temp_path = "/tmp/docker-compose.yml.tmp"
    final_path = "/var/www/och/docker-compose.yml"
    
    print(f"Connecting to {host} via SFTP...")
    try:
        transport = paramiko.Transport((host, 22))
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        print(f"Uploading {local_path} to {remote_temp_path}...")
        sftp.put(local_path, remote_temp_path)
        sftp.close()
        transport.close()
        
        print("Upload successful. Moving to production path with sudo...")
        # Use SSH to move it with sudo
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # We use sudo tee to move and overwrite
        cmd = f"echo 'Ongoza@#1' | sudo -S mv {remote_temp_path} {final_path}"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # Verify
        stdin, stdout, stderr = client.exec_command(f"ls -l {final_path}")
        print(f"Final file status: {stdout.read().decode()}")
        
        # Restart
        print("Rebooting ecosystem...")
        stdin, stdout, stderr = client.exec_command(f"cd /var/www/och && echo 'Ongoza@#1' | sudo -S docker-compose up -d --remove-orphans")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        client.close()
        print("SUCCESS: Infrastructure restored and ecosystem rebooting.")
        
    except Exception as e:
        print(f"ERROR during SFTP restoration: {e}")

if __name__ == "__main__":
    sftp_restore()
