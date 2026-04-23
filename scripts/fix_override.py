import os
import paramiko

def fix_override():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Read the file
    stdin, stdout, stderr = client.exec_command('cat /var/www/och/docker-compose.override.yml')
    content = stdout.read().decode()
    
    # Remove the postgres-relational block
    lines = content.splitlines()
    new_lines = []
    skip = 0
    for line in lines:
        if skip > 0:
            skip -= 1
            continue
        if 'postgres-relational:' in line:
            skip = 2 # skip the header and the next 2 lines (ports)
            continue
        new_lines.append(line)
    
    new_content = '\n'.join(new_lines)
    
    # Write the file back
    sftp = client.open_sftp()
    with sftp.open('/var/www/och/docker-compose.override.yml', 'w') as f:
        f.write(new_content)
    sftp.close()
    
    print("Fixed docker-compose.override.yml")
    client.close()

if __name__ == "__main__":
    fix_override()
