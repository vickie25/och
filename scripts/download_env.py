import os
import paramiko

def download_env():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username=user, password=password, timeout=10)
        
        # Download
        sftp = c.open_sftp()
        sftp.get('/var/www/och/.env', 'remote_production.env')
        sftp.close()
        c.close()
        print("Downloaded .env successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    download_env()
