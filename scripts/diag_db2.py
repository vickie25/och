import paramiko

script = """
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import DeviceTrust

try:
    print('Testing User...')
    User = get_user_model()
    u = User.objects.filter(email='mystartupkenya@gmail.com').first()
    print('User found:', u.email if u else 'None')
    
    if u:
        print('Testing DeviceTrust...')
        device = DeviceTrust.objects.filter(user=u).first()
        print('DeviceTrust query succeeded')
        
        # Try creating one to see if insert works
        DeviceTrust.objects.get_or_create(user=u, device_id='test-123')
        print('DeviceTrust create succeeded')

except Exception as e:
    import traceback
    print("Database Exception Occurred:", e)
    traceback.print_exc()
"""

def execute():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('69.30.235.220', username='administrator', password='Ongoza@#1', timeout=5)
        
        def run_sudo(cmd):
            stdin, stdout, stderr = c.exec_command(f'printf "Ongoza@#1\\n" | sudo -S -p "" {cmd}')
            return stdout.read().decode('utf-8').strip(), stderr.read().decode('utf-8').strip()
            
        write_cmd = f"cat << 'EOF' > /tmp/diag_db2.py\n{script}\nEOF"
        c.exec_command(write_cmd)
        
        run_sudo("docker cp /tmp/diag_db2.py hub_prod_django:/app/diag_db2.py")
        out, err = run_sudo("docker exec hub_prod_django python /app/diag_db2.py")
        print("OUTPUT:\\n", out)
        if err: print("ERR:\\n", err)
        
    except Exception as e:
        print('Failed:', e)

if __name__ == '__main__':
    execute()
