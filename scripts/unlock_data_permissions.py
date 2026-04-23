import paramiko

def unlock_data_permissions():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Unlocking production volume permissions on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # We chown the volumes to 999:999 (the postgres user UID inside the container)
        # This resolves the "No Databases" issue and unlocks the production records.
        vols = ['och_postgres_data', 'och_django_media', 'ongozacyberhub_postgres_data']
        
        for vol in vols:
            print(f"Unlocking: {vol}")
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' chown -R 999:999 /var/lib/docker/volumes/{vol}/_data"
            client.exec_command(cmd, get_pty=True)
        
        # Final stack restart to pick up the new permissions
        print("Restarting stack with unlocked data...")
        cmd = f"cd /var/www/och && printf '%s\\n' '{password}' | sudo -S -p '' docker-compose -p hub_prod up -d"
        client.exec_command(cmd, get_pty=True)
        
        client.close()
        print("Unlock Complete.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    unlock_data_permissions()
