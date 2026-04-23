import os
import paramiko

def check_table_columns():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    python_cmd = """
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'curriculum_tracks'")
    columns = [row[0] for row in cursor.fetchall()]
    print(columns)
"""
    # Create a temporary script file on the VPS
    client.exec_command(f"echo '{python_cmd}' > /tmp/check_columns.py")
    
    # Run it inside the django container
    cmd = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker cp /tmp/check_columns.py hub_prod_django:/app/check_columns.py"
    client.exec_command(cmd)
    
    cmd2 = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_django python manage.py shell < /tmp/check_columns.py"
    # Actually simpler:
    cmd2 = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_django python manage.py shell -c \"from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT inet_server_addr(), inet_server_port()'); print('Server Addr/Port:', cursor.fetchone())\""
    
    stdin, stdout, stderr = client.exec_command(cmd2)
    
    print("--- Table Columns ---")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_table_columns()
