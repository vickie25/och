import paramiko

def volume_size_hunt():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Hunting for the data-heavy volume on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # We check the size of the volumes in /var/lib/docker/volumes (standard path)
        # Note: We need sudo to see these
        vols = ['ongozacyberhub_postgres_data', 'och_postgres_data', 'ongoza_postgres_data', 'hub_prod_postgres_data']
        
        print("\n--- VOLUME SIZE REPORT ---")
        for vol in vols:
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' du -sh /var/lib/docker/volumes/{vol} 2>/dev/null || echo '{vol}: Not Accessible'"
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            print(stdout.read().decode('utf-8', errors='ignore').strip())
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    volume_size_hunt()
