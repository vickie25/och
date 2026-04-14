import paramiko

def patch_remote_env():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # Commands to patch the .env file on the server
        # We replace the broken port and encryption settings
        patch_commands = [
            f"printf '{password}\\n' | sudo -S -p '' sed -i 's/MAIL_PORT=465/MAIL_PORT=587/g' /var/www/och/backend/django_app/.env",
            f"printf '{password}\\n' | sudo -S -p '' sed -i 's/MAIL_ENCRYPTION=ssl/MAIL_ENCRYPTION=tls/g' /var/www/och/backend/django_app/.env"
        ]
        
        for cmd in patch_commands:
            print(f"Executing: {cmd[:40]}...")
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            stdout.read() # Wait for completion
            
        print("Remote .env file patched successfully.")
        
        # Verify the patch
        print("\nVerifying patch...")
        command = "grep -E 'MAIL_PORT|MAIL_ENCRYPTION' /var/www/och/backend/django_app/.env"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    patch_remote_env()
