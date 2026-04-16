import paramiko
import time

host = "69.30.235.220"
ssh_user = "administrator"
password = "Ongoza@#1"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=ssh_user, password=password)

# Write Django management command to container
script = """import sys
sys.stdout.flush()
from users.models import User, UserRole
from users.auth_models import MFAMethod

print("SUPERUSERS:", flush=True)
for u in User.objects.filter(is_superuser=True):
    print(f"  {u.email} | {u.account_status} | mfa_enabled={u.mfa_enabled} | mfa_method={u.mfa_method}", flush=True)

print("ADMIN ROLE USERS:", flush=True)
for ur in UserRole.objects.filter(role__name="admin", is_active=True).select_related("user"):
    u = ur.user
    methods = list(MFAMethod.objects.filter(user=u).values_list("method_type","enabled"))
    print(f"  {u.email} | {u.account_status} | mfa_enabled={u.mfa_enabled} | mfa_method={u.mfa_method} | methods={methods}", flush=True)
sys.stdout.flush()
"""

sftp = client.open_sftp()
with sftp.file('/tmp/acheck.py', 'w') as f:
    f.write(script)
sftp.close()

# Copy into container
stdin, stdout, stderr = client.exec_command("docker cp /tmp/acheck.py ongozacyberhub_django:/tmp/acheck.py")
time.sleep(2)
print(stdout.read().decode())

# Run directly with python -c using the shell script via stdin pipe trick
transport = client.get_transport()
channel = transport.open_session()
channel.get_pty()
channel.exec_command("docker exec -w /app ongozacyberhub_django python manage.py shell -c \"exec(open('/tmp/acheck.py').read())\"")

output = ""
for _ in range(30):
    time.sleep(0.5)
    while channel.recv_ready():
        output += channel.recv(4096).decode(errors='replace')
    if channel.exit_status_ready():
        break

while channel.recv_ready():
    output += channel.recv(4096).decode(errors='replace')

print(output)
client.close()
