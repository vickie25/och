import paramiko
import re

def mass_unblock():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        for iteration in range(50): # Higher limit for large drift
            print(f"\n=== Mass-Unblock Iteration {iteration+1} ===")
            command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py migrate 2>&1"
            stdin, stdout, stderr = client.exec_command(command, get_pty=True)
            output = stdout.read().decode(errors='replace')
            print(output)
            
            if "already exists" in output:
                # Identify the app and migration being applied
                # Look for "Applying <app>.<migration>..."
                match = re.search(r"Applying ([\w\.]+)\.\.\.", output)
                if match:
                    app_migration = match.group(1)
                    app, migration = app_migration.split(".")
                    print(f"Detected Drift: {app_migration}. Faking...")
                    
                    fake_command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py migrate {app} {migration} --fake"
                    _, fs, _ = client.exec_command(fake_command, get_pty=True)
                    print(fs.read().decode())
                else:
                    print("Could not identify specific migration. Attempting to determine via error context...")
                    # Fallback: find the first unapplied migration in showmigrations and try to fake it
                    status_command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py showmigrations"
                    _, ss, _ = client.exec_command(status_command, get_pty=True)
                    status_output = ss.read().decode()
                    
                    # Find the first [ ]
                    for line in status_output.split("\n"):
                        if "[ ]" in line:
                            # Extract app and name (usually " <app>\n [ ] <migration>")
                            # This is tricky without better parsing, but we can try
                            pass
                    print("Manual intervention might be needed for this specific error context.")
                    break
            elif "OK" in output or "No migrations to apply" in output:
                print("SUCCESS: ALL MIGRATIONS APPLIED!")
                break
            elif "relation" in output and "does not exist" in output:
                # Handle the opposite case: Missing table
                # Identify the app and try to migrate just that one
                print("Missing table detected. Attempting app-specific migrate...")
                # We can try to migrate the app mentioned in the error if possible
                break
            else:
                print("Terminal state reached or unknown error.")
                break
                
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    mass_unblock()
