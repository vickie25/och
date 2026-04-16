import paramiko
import time

host = "69.30.235.220"
ssh_user = "administrator"
password = "Ongoza@#1"

# Script to run inside Django container
# Clears broken MFA state for 3 blocked admins
# Does NOT touch kelvin.reallife8@gmail.com
django_script = """from users.models import User
from users.auth_models import MFAMethod

# Only fix these 3 — they have mfa_enabled=True but NO MFAMethod records
blocked_emails = [
    'nelsonochieng516@gmail.com',
    'wilsonndambuki47@gmail.com',
    'mwangmrtin@gmail.com',
]

fixed = 0
for email in blocked_emails:
    try:
        user = User.objects.get(email=email)
        # Verify they truly have no MFAMethod records
        method_count = MFAMethod.objects.filter(user=user, enabled=True).count()
        if method_count == 0 and user.mfa_enabled:
            user.mfa_enabled = False
            user.mfa_method = None
            user.save(update_fields=['mfa_enabled', 'mfa_method'])
            print(f'FIXED: {email} - cleared orphaned mfa_enabled flag')
            fixed += 1
        elif method_count > 0:
            print(f'SKIP: {email} - has {method_count} real MFA method(s), leaving untouched')
        else:
            print(f'OK: {email} - mfa_enabled already False')
    except User.DoesNotExist:
        print(f'NOT FOUND: {email}')

print(f'Done. Fixed {fixed} accounts.')

# Verify kelvin is untouched
try:
    kelvin = User.objects.get(email='kelvin.reallife8@gmail.com')
    print(f'kelvin status: mfa_enabled={kelvin.mfa_enabled}, account_status={kelvin.account_status}')
except:
    print('kelvin: not found')
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=ssh_user, password=password)

# Write script to server, copy into container, run it
sftp = client.open_sftp()
with sftp.file('/tmp/fix_mfa.py', 'w') as f:
    f.write(django_script)
sftp.close()

transport = client.get_transport()

# Copy into container
ch1 = transport.open_session()
ch1.exec_command("docker cp /tmp/fix_mfa.py ongozacyberhub_django:/tmp/fix_mfa.py")
time.sleep(2)
ch1.recv_exit_status()

# Run
ch2 = transport.open_session()
ch2.get_pty()
ch2.exec_command("docker exec -w /app ongozacyberhub_django python manage.py shell -c \"exec(open('/tmp/fix_mfa.py').read())\"")

output = ""
for _ in range(40):
    time.sleep(0.5)
    while ch2.recv_ready():
        output += ch2.recv(4096).decode(errors='replace')
    if ch2.exit_status_ready():
        break
while ch2.recv_ready():
    output += ch2.recv(4096).decode(errors='replace')

print(output)
client.close()
