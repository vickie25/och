import paramiko

host = "69.30.235.220"
user = "administrator"
password = "Ongoza@#1"

try:
    print("Testing ping and fetching specific iptables rules...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=60)
    
    def run_sudo(cmd):
        stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}")
        return stdout.read().decode('utf-8', 'ignore').strip()

    print("\nPing Check:")
    print(run_sudo("ping -c 3 138.197.203.235"))
    
    print("\nIptables Check for 138:")
    print(run_sudo("iptables -L -n -v | grep 138.197"))

    client.close()
except Exception as e:
    print(f"Error: {e}")
