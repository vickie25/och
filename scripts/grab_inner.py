import os
import paramiko

def grab_inner():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        # Copy inner .env to user's home dir to avoid permission issues
        c.exec_command(f'echo "{password}" | sudo -S cp /var/www/och/backend/django_app/.env /home/administrator/django.env')
        c.exec_command(f'echo "{password}" | sudo -S chown administrator:administrator /home/administrator/django.env')
        
        # Download
        sftp = c.open_sftp()
        sftp.get('/home/administrator/django.env', 'django.env')
        sftp.close()
        c.close()
        print("Downloaded inner django.env")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    grab_inner()
