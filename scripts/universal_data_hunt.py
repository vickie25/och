import paramiko

def universal_data_hunt():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Initiating Universal Volume Scan on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Get ALL volumes
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker volume ls --format '{{{{.Name}}}}'"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        volumes = stdout.read().decode('utf-8', errors='ignore').splitlines()
        
        print(f"Found {len(volumes)} volumes. Scanning each for the production database...")
        
        for vol in volumes:
            vol = vol.strip()
            if not vol: continue
            
            # 2. Check table count in each (looking for >50 tables)
            # Use postgres:16-alpine since we know the data is V16
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v {vol}:/var/lib/postgresql/data postgres:16-alpine sh -c \"sleep 4 && psql -U postgres -d ongozacyberhub -t -c 'SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = \\'public\\'' 2>/dev/null || echo '0'\""
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            count_str = stdout.read().decode('utf-8', errors='ignore').strip()
            
            # We also check the 'postgres' database just in case it was renamed
            if count_str == "0":
                cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v {vol}:/var/lib/postgresql/data postgres:16-alpine sh -c \"sleep 4 && psql -U postgres -d postgres -t -c 'SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = \\'public\\'' 2>/dev/null || echo '0'\""
                stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
                count_str = stdout.read().decode('utf-8', errors='ignore').strip()

            if count_str.isdigit() and int(count_str) > 10:
                print(f"!!! POTENTIAL WINNER !!! Volume: {vol} has {count_str} tables.")
            else:
                # print(f"Volume {vol}: {count_str} tables.")
                pass
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    universal_data_hunt()
