import paramiko
import re
import time

def auto_unblock():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        for i in range(20): # Limit retries to prevent infinite loops
            print(f"\n=== Sync Attempt {i+1} ===")
            command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py migrate 2>&1"
            stdin, stdout, stderr = client.exec_command(command, get_pty=True)
            output = stdout.read().decode(errors='replace')
            print(output)
            
            if "already exists" in output:
                # Extract the app and migration name if possible
                # Django output usually looks like: "Applying <app>.<migration>... FAILED"
                match = re.search(r"Applying ([\w\.]+)\.\.\. FAILED", output)
                if match:
                    app_migration = match.group(1)
                    app, migration = app_migration.split(".")
                    print(f"Detected blocker: {app_migration}. Faking it...")
                    
                    fake_command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py migrate {app} {migration} --fake"
                    _, fs, _ = client.exec_command(fake_command, get_pty=True)
                    print(fs.read().decode())
                    continue
                else:
                    # Generic case: try to fake-initial or identify based on the error
                    print("Could not identify specific migration to fake. Attempting to determine app...")
                    # Sometimes the error mentions the table, we can infer the app but it's risky
                    print("Please check the output above and manually fake if needed. Stopping auto-unblock.")
                    break
            elif "OK" in output or "No migrations to apply" in output:
                print("Synchronization Successful!")
                break
            else:
                print("Unknown error or success. Stopping.")
                break
                
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    auto_unblock()
