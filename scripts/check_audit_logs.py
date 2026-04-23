import os
import paramiko

def check_audit_logs():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Check AuditLog for the test email
    script = """
from users.audit_models import AuditLog
from django.utils import timezone
import datetime

one_hour_ago = timezone.now() - datetime.timedelta(hours=1)
logs = AuditLog.objects.filter(actor_identifier='kelvinmaina202@gmail.com', timestamp__gte=one_hour_ago).order_by('-timestamp')
if not logs.exists():
    # Try just searching for 'login' failures in the last hour
    logs = AuditLog.objects.filter(action='login', result='failure', timestamp__gte=one_hour_ago).order_by('-timestamp')

for log in logs[:10]:
    print(f'Time: {log.timestamp} | Action: {log.action} | Result: {log.result} | Meta: {log.metadata}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_audit_logs()
