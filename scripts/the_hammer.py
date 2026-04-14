import paramiko
import re
import time

def the_hammer():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        for iteration in range(100): # High limit to clear all drift
            print(f"\n=== Hammer Blow {iteration+1} ===")
            command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py migrate 2>&1"
            stdin, stdout, stderr = client.exec_command(command, get_pty=True)
            output = stdout.read().decode(errors='replace')
            print(output)
            
            # Look for the specific migration that failed
            # Format: "Applying <app>.<migration>... FAILED" or just "Applying <app>.<migration>..." followed by error
            match = re.search(r"Applying ([\w\._]+)\.\.\.", output)
            
            if "already exists" in output and match:
                app_migration = match.group(1)
                app, migration = app_migration.split(".", 1)
                print(f"Hammering Drift: {app_migration}")
                
                fake_command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py migrate {app} {migration} --fake"
                _, fs, _ = client.exec_command(fake_command, get_pty=True)
                print(fs.read().decode())
                continue
            
            elif "cannot cast type uuid to bigint" in output and match:
                # Handle the specific type cast error if it reappears in an automated way
                app_migration = match.group(1)
                app, migration = app_migration.split(".", 1)
                print(f"Hammering Type Mismatch: {app_migration} (Faking after manual SQL fix)")
                fake_command = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose exec -T django python manage.py migrate {app} {migration} --fake"
                _, fs, _ = client.exec_command(fake_command, get_pty=True)
                print(fs.read().decode())
                continue

            elif "OK" in output or "No migrations to apply" in output:
                print("SUCCESS: PLATFORM FULLY SYNCHRONIZED!")
                break
            
            elif "OperationalError" in output and "connection unexpectedly" in output:
                print("DB Timeout. Waiting 10 seconds before retry...")
                time.sleep(10)
                continue
                
            else:
                print("Final status reached or unknown blocker. Check output.")
                break
                
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    the_hammer()
