import paramiko

def fix_ports():
    host = '69.30.235.220'
    username = 'administrator'
    password = 'Ongoza@#1'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, 22, username, password)
    
    # Update ports to standard 80 and 443
    ssh.exec_command("sed -i 's/NGINX_HTTP_PORT=.*/NGINX_HTTP_PORT=80/' /var/www/och/.env")
    ssh.exec_command("sed -i 's/NGINX_HTTPS_PORT=.*/NGINX_HTTPS_PORT=443/' /var/www/och/.env")
    
    # Restart docker-compose
    ssh.exec_command("cd /var/www/och && docker-compose up -d")
    print("Ports fixed and server restarted.")
    ssh.close()

if __name__ == "__main__":
    fix_ports()
