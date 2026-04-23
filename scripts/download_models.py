import paramiko

def execute():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('69.30.235.220', username='administrator', password='Ongoza@#1', timeout=5)
        
        sftp = c.open_sftp()
        sftp.get('/var/www/och/backend/django_app/users/models.py', 'models.py')
        print("Successfully downloaded users/models.py")
        sftp.close()
        
    except Exception as e:
        print('Failed:', e)

if __name__ == '__main__':
    execute()
