import paramiko

def nuclear_permission_reset():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Executing Nuclear Permission Reset on production data...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # Resetting both Ownership AND Permissions recursively to ensure nothing is blocked
        vols = ['och_postgres_data', 'och_django_media']
        
        for vol in vols:
            print(f"Resetting: {vol}")
            # Chown to postgres:postgres and Chmod to standard postgres data permissions
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' sh -c 'chown -R 999:999 /var/lib/docker/volumes/{vol}/_data && chmod -R 700 /var/lib/docker/volumes/{vol}/_data'"
            client.exec_command(cmd, get_pty=True)
        
        # Restart the database container ONLY for speed
        print("Restarting database engine...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker restart hub_prod_postgres"
        client.exec_command(cmd, get_pty=True)
        
        client.close()
        print("Nuclear Reset Complete.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    nuclear_permission_reset()
