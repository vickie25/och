import paramiko

host = "69.30.235.220"
user = "administrator"
current_password = "Ongoza@#1"
new_password = "0ngoz@_Cyber_2026_Secure!"

try:
    print("Changing password for administrator...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=current_password, timeout=60)
    
    # Use sudo to change the administrator password
    cmd = f"printf '%s\\n' '{current_password}' | sudo -S -p '' chpasswd << EOF\nadministrator:{new_password}\nEOF"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    err = stderr.read().decode('utf-8').strip()
    out = stdout.read().decode('utf-8').strip()
    
    if err and "password" not in err.lower():
         print("Stderr:", err)
         
    print("Successfully changed password to:", new_password)
    
    # Let's verify we can connect with the new password
    client.close()
    
    test_client = paramiko.SSHClient()
    test_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    test_client.connect(host, username=user, password=new_password, timeout=60)
    print("Verification: Successfully logged in with new password.")
    test_client.close()

except Exception as e:
    print(f"Error: {e}")
