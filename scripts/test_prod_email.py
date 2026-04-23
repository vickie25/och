import os
import paramiko

def test_production_email():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    script = """
from django.core.mail import send_mail
try:
    res = send_mail(
        'Ongoza Production Test',
        'If you receive this, the production email system is working.',
        'info@cresdynamics.com',
        ['kelvinmaina202@gmail.com'],
        fail_silently=False,
    )
    print(f'SUCCESS: Email sent (result={res})')
except Exception as e:
    print(f'ERROR: {str(e)}')
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i hub_prod_django python manage.py shell << 'EOF'\n{script}\nEOF")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    test_production_email()
