import paramiko

def debug_server():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # Get the very last lines of the Django log to see the DB error message
        print("=== Final Database Error Message ===")
        command = f"printf '%s\\n' '{password}' | sudo -S -p '' docker logs ongozacyberhub_django --tail 50"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    debug_server()
