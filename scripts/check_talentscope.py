import os
import paramiko

def check_table():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    cmd = 'docker exec hub_prod_django python manage.py shell -c "from talentscope.models import BehaviorSignal; print(\'Table exists!\')"'
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    
    if "ProgrammingError" in err or "does not exist" in err:
        print("TABLE DOES NOT EXIST!")
        print(err)
    else:
        print(out)
        
    client.close()

if __name__ == "__main__":
    check_table()
