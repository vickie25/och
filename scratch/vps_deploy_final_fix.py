import paramiko
import time

def deploy_to_vps():
    host = "69.30.235.220"
    user = "administrator"
    pw = "Ongoza@#1"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    ssh.connect(host, 22, user, pw)
    
    # Check if build is finished by pulling
    print("Pulling latest images from GHCR...")
    stdin, stdout, stderr = ssh.exec_command("docker pull ghcr.io/cresdynamics-lang/och-nextjs:latest")
    pull_output = stdout.read().decode('utf-8')
    print(pull_output)
    
    if "Image is up to date" in pull_output:
        print("Build might still be in progress or image is already updated.")
    
    print("Restarting nextjs service...")
    # Using 'up -d' will only recreate if the image/config changed
    stdin, stdout, stderr = ssh.exec_command("docker-compose up -d nextjs")
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    
    print("Pruning old images to save space...")
    ssh.exec_command("docker image prune -f")
    
    ssh.close()
    print("Deployment finished.")

if __name__ == "__main__":
    deploy_to_vps()
