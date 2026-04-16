import paramiko

def get_mfa_and_admin_info():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("=== SEARCHING FOR MFA/OTP CODES IN DJANGO LOGS ===")
        # Search specifically for BACKUP OTP LOG entries
        command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker logs ongozacyberhub_django --tail 200 2>&1 | grep -E 'BACKUP|OTP|mfa|MFA|code|CODE|admin' | tail -40"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        output = stdout.read().decode()
        print(output if output.strip() else "No MFA code lines found in recent logs.")
        
        print("\n=== CHECKING ADMIN USER MFA STATUS IN DATABASE ===")
        command2 = f"""printf '%s\\n' '{password}' | sudo -S -p '' docker exec ongozacyberhub_django python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()
from users.models import User
from users.auth_models import MFAMethod
try:
    admin = User.objects.filter(is_superuser=True).first() or User.objects.filter(roles__role__name='admin').first()
    if admin:
        print('Admin email:', admin.email)
        print('MFA enabled:', admin.mfa_enabled)
        print('MFA method:', admin.mfa_method)
        print('Account status:', admin.account_status)
        methods = MFAMethod.objects.filter(user=admin)
        for m in methods:
            print(f'  Method: {{m.method_type}}, enabled={{m.enabled}}, verified={{m.is_verified}}')
    else:
        print('No admin user found')
except Exception as e:
    print('Error:', str(e))
"
"""
        stdin2, stdout2, stderr2 = client.exec_command(command2, get_pty=True)
        import time
        time.sleep(5)
        out2 = stdout2.read().decode()
        err2 = stderr2.read().decode()
        print(out2)
        if err2.strip():
            print("STDERR:", err2[:500])
        
        client.close()
    except Exception as e:
        print(f"Connection Error: {str(e)}")

if __name__ == "__main__":
    get_mfa_and_admin_info()
