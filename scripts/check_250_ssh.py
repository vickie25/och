import os
import paramiko

def check_ssh(host, user, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=10)
        
        stdin, stdout, stderr = client.exec_command("whoami && hostname")
        out = stdout.read().decode('utf-8', 'ignore')
        print(f"SUCCESS on {host} as {user}: {out.strip()}")
        client.close()
    except Exception as e:
        print(f"FAILED on {host} as {user}: {e}")

if __name__ == "__main__":
    # Test .250 with standard credentials
    check_ssh("38.247.138.250", "administrator", os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    check_ssh("38.247.138.250", "root", os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
