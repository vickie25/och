import os
import paramiko

def fix_override_sudo():
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
            skip = 2 
            continue
        new_lines.append(line)
    
    new_content = '\n'.join(new_lines)
    
    # Write to a temp file
    sftp = client.open_sftp()
    with sftp.open('/tmp/override_new', 'w') as f:
        f.write(new_content)
    sftp.close()
    
    # Use sudo to move it
    client.exec_command('echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S mv /tmp/override_new /var/www/och/docker-compose.override.yml')
    
    print("Fixed docker-compose.override.yml with sudo")
    client.close()

if __name__ == "__main__":
    fix_override_sudo()
