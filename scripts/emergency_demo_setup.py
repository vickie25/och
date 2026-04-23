import paramiko

def emergency_demo_setup():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Setting up Emergency Demo Environment...")
    try:
        client.connect(host, username=user, password=password, timeout=30)
        
        # 1. Create Superuser (Environmental)
        print("Creating administrator account...")
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec -i hub_prod_django python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('administrator', 'admin@ongozacyberhub.africa', 'Ongoza@#1') if not User.objects.filter(username='administrator').exists() else None\""
        client.exec_command(cmd, get_pty=True)

        # 2. Inject a Demo Cohort via SQL
        print("Injecting Demo Cohort...")
        sql = "INSERT INTO cohorts (name, description, status, start_date) VALUES ('Demo Cohort April 2026', 'Restored environment for the 9PM demo.', 'active', '2026-04-19') ON CONFLICT DO NOTHING;"
        cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' docker exec -i hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"{sql}\" || echo 'Cohort table empty, skipping injection.'"
        client.exec_command(cmd, get_pty=True)
        
        client.close()
        print("Emergency Setup Complete.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    emergency_demo_setup()
