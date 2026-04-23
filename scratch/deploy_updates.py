import paramiko
import os

def sftp_deploy():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    print(f"Connecting to {host} via SFTP...")
    try:
        transport = paramiko.Transport((host, 22))
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # 1. Upload views.py
        local_views = "backend/django_app/coaching/views.py"
        remote_views = "/var/www/och/backend/django_app/coaching/views.py"
        print(f"Uploading {local_views} to {remote_views}...")
        sftp.put(local_views, "/tmp/views_temp.py")
        
        # 2. Upload clear_kelvin.py
        local_clear = "scratch/clear_kelvin.py"
        remote_clear = "/var/www/och/backend/django_app/scripts/clear_kelvin.py"
        print(f"Uploading {local_clear} to {remote_clear}...")
        sftp.put(local_clear, "/tmp/clear_temp.py")
        
        sftp.close()
        transport.close()
        
        print("Upload successful. Moving to production path with sudo...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # Move views.py
        cmd1 = f"echo 'Ongoza@#1' | sudo -S mv /tmp/views_temp.py {remote_views} && sudo -S chown administrator:administrator {remote_views}"
        client.exec_command(cmd1)
        
        # Move clear_kelvin.py
        cmd2 = f"echo 'Ongoza@#1' | sudo -S mkdir -p /var/www/och/backend/django_app/scripts && echo 'Ongoza@#1' | sudo -S mv /tmp/clear_temp.py {remote_clear} && sudo -S chown administrator:administrator {remote_clear}"
        client.exec_command(cmd2)
        
        # Restart Django
        print("Restarting Django container for hot reload...")
        stdin, stdout, stderr = client.exec_command(f"cd /var/www/och && echo 'Ongoza@#1' | sudo -S docker-compose restart django")
        print(stdout.read().decode())
        
        # Run clear_kelvin.py
        print("Running clear_kelvin.py inside Django container...")
        stdin, stdout, stderr = client.exec_command(f"cd /var/www/och && echo 'Ongoza@#1' | sudo -S docker-compose exec -T django python scripts/clear_kelvin.py")
        print(stdout.read().decode())
        if stderr.read().decode():
            print(f"STDERR: {stderr.read().decode()}")
        
        client.close()
        print("SUCCESS: Django patched and Kevin's data cleared.")
        
    except Exception as e:
        print(f"ERROR during SFTP deploy: {e}")

if __name__ == "__main__":
    sftp_deploy()
