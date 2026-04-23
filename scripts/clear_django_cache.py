import paramiko

def clear_django_cache():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    django_script = """
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.core.cache import cache

print("Clearing global Django cache (Removes rate limiting buckets)...")
cache.clear()
print("Cache flushed successfully!")
"""

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # Save script
        client.exec_command(f"cat << 'EOF' > /tmp/clear_cache.py\n{django_script}\nEOF")
        
        # Execute inside django container
        command = "sudo docker exec -i hub_prod_django python3 -"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        
        stdin.write(django_script)
        stdin.close()
        
        print("\n--- [FLUSHING THROTTLE/CACHE] ---")
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clear_django_cache()
