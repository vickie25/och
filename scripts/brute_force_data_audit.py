import paramiko
import time

def brute_force_data_audit():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    potential_vols = ['ongozacyberhub_postgres_data', 'och_postgres_data', 'ongoza_postgres_data']
    
    print("Brute-forcing volume verification on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        for vol in potential_vols:
            print(f"\nTesting Volume: {vol}")
            # we update the compose file on the server (temp fix) to use this volume
            # but simpler: just run a temporary postgres container mapped to this volume
            cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker run --rm -v {vol}:/var/lib/postgresql/data postgres:15-alpine sh -c \"sleep 5 && psql -U postgres -d ongozacyberhub -t -c 'SELECT COUNT(*) FROM users' 2>/dev/null || echo 'FAIL'\""
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            result = stdout.read().decode('utf-8', errors='ignore').strip()
            print(f"Result for {vol}: {result}")
            
            if 'FAIL' not in result and result.strip().isdigit() and int(result.strip()) > 0:
                print(f"!!! SUCCESS !!! Volume {vol} contains {result} users.")
                break
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    brute_force_data_audit()
