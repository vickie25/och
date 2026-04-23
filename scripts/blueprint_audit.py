import paramiko

def blueprint_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print("Executing Blueprint Audit...")
    try:
        client.connect(host, username=user, password=password, timeout=120)
        
        # Read the full docker-compose.yml
        print("\n--- MASTER DOCKER-COMPOSE ---")
        stdin, stdout, stderr = client.exec_command("cat /var/www/och/docker-compose.yml")
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    blueprint_audit()
