import paramiko

host = "69.30.235.220"
user = "administrator"
password = "Ongoza@#1"

try:
    print("Connecting to host...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=60)
    
    def run_sudo(cmd):
        stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}")
        return stdout.read().decode('utf-8', 'ignore').strip()

    print("\n1. Querying Real Database for Users...")
    query = """
from django.contrib.auth import get_user_model
User = get_user_model()
users = User.objects.filter(email__in=['kelvin202maina@gmail.com', 'kelvin.reallife8@gmail.com'])
if not users.exists():
    print('USER_NOT_FOUND_IN_DB')
else:
    for u in users:
        print(f'FOUND: {u.email} | Role: {getattr(u, "role", "No role attr")} | Active: {u.is_active} | Superuser: {u.is_superuser}')
    print(f'Total users in DB: {User.objects.count()}')
"""
    # Just run it using -c directly, properly quoted
    encoded_query = query.replace('\n', '; ').replace(';;', ';')
    db_out = run_sudo(f"docker exec hub_prod_django python manage.py shell -c \"{encoded_query}\"")
    print(db_out)

    print("\n2. Strengthening System Defenses with fail2ban...")
    print(run_sudo("apt-get update > /dev/null 2>&1"))
    print(run_sudo("DEBIAN_FRONTEND=noninteractive apt-get install fail2ban -y > /dev/null 2>&1"))
    print(run_sudo("systemctl enable fail2ban > /dev/null 2>&1"))
    print(run_sudo("systemctl start fail2ban > /dev/null 2>&1"))
    print("Fail2ban Installed and Started. Future brute-force attacks will be automatically banned.")

    client.close()
except Exception as e:
    print(f"Error: {e}")
