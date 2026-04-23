import os
import paramiko

def check_db():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Check StudentAnalytics
    cmd = 'docker exec hub_prod_django python manage.py shell -c "from coaching.models import StudentAnalytics; print(f\'StudentAnalytics count: {StudentAnalytics.objects.count()}\')"'
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    # Check for missing tables/migrations
    cmd = 'docker exec hub_prod_django python manage.py showmigrations'
    stdin, stdout, stderr = client.exec_command(cmd)
    print("MIGRATIONS STATUS:")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_db()
