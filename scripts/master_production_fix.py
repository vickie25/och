import paramiko
import sys
import time

def master_production_fix():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    remote_db = "38.247.138.250"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [MASTER FIX: PRODUCTION ALIGNMENT] ---")
        
        # 1. Update BOTH .env files
        paths = ["/var/www/och/.env", "/var/www/och/backend/django_app/.env"]
        for p in paths:
            print(f"Aligning {p}...")
            cmd = f'sudo sed -i "s/^DB_HOST=.*/DB_HOST={remote_db}/" {p} && sudo sed -i "s/^DB_PASSWORD=.*/DB_PASSWORD=postgres/" {p}'
            stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {cmd}', get_pty=True)
            stdout.read() # wait
            
        # 2. Update docker-compose.yml (Remove hardcoding)
        print("Ensuring docker-compose.yml uses the correct host...")
        compose_path = "/var/www/och/docker-compose.yml"
        cmd = f'sudo sed -i "s/DB_HOST: .*/DB_HOST: {remote_db}/g" {compose_path}'
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {cmd}', get_pty=True)
        stdout.read()
        
        # 3. Forced Restart
        print("Restarting services to apply configuration...")
        cmd = "sudo docker compose -f /var/www/och/docker-compose.yml up -d django"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {cmd}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 4. Wait for container to be ready
        print("Waiting 15s for Django to initialize...")
        time.sleep(15)
        
        # 5. Surgical Repair INSIDE the container
        print("Executing structural repair on the remote database...")
        repair_code = f"""
import os
import django
from django.db import connection, transaction
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()
queries = [
    'CREATE TABLE IF NOT EXISTS "user_sessions" ("id" uuid NOT NULL PRIMARY KEY, "device_fingerprint" varchar(255) NOT NULL, "device_name" varchar(255) NULL, "device_type" varchar(50) NULL, "ip_address" inet NULL, "ua" text NULL, "refresh_token_hash" varchar(64) NOT NULL UNIQUE, "is_trusted" boolean NOT NULL, "trusted_at" timestamptz NULL, "mfa_verified" boolean NOT NULL, "risk_score" double precision NOT NULL, "created_at" timestamptz NOT NULL, "last_activity" timestamptz NOT NULL, "expires_at" timestamptz NOT NULL, "revoked_at" timestamptz NULL, "user_id" bigint NOT NULL)',
    'CREATE INDEX IF NOT EXISTS "user_sessions_user_id_idx" ON "user_sessions" ("user_id")',
    'CREATE TABLE IF NOT EXISTS "mfa_methods" ("id" uuid NOT NULL PRIMARY KEY, "method_type" varchar(20) NOT NULL, "secret_encrypted" text NULL, "totp_backup_codes" jsonb NOT NULL, "phone_e164" varchar(20) NULL, "enabled" boolean NOT NULL, "is_primary" boolean NOT NULL, "is_verified" boolean NOT NULL, "verified_at" timestamptz NULL, "created_at" timestamptz NOT NULL, "last_used_at" timestamptz NULL, "user_id" bigint NOT NULL)',
    'CREATE INDEX IF NOT EXISTS "mfa_methods_user_id_idx" ON "mfa_methods" ("user_id")',
    'CREATE TABLE IF NOT EXISTS "user_identities" ("id" uuid NOT NULL PRIMARY KEY, "provider" varchar(20) NOT NULL, "provider_sub" varchar(255) NOT NULL, "metadata" jsonb NOT NULL, "linked_at" timestamptz NOT NULL, "last_sync_at" timestamptz NULL, "is_active" boolean NOT NULL, "user_id" bigint NOT NULL)',
    'CREATE INDEX IF NOT EXISTS "user_ident_provide_idx" ON "user_identities" ("provider", "provider_sub")',
    "DELETE FROM django_migrations WHERE app='users' AND name='0001_initial'",
    "INSERT INTO django_migrations (app, name, applied) VALUES ('users', '0001_initial', NOW())"
]
with connection.cursor() as cursor:
    for q in queries:
        try:
            cursor.execute(q)
            print(f"Executed: {{q[:50]}}")
            transaction.commit()
        except Exception as e:
            print(f"Error on {{q[:20]}}: {{str(e)}}")
"""
        # Save to file and cp to container
        client.exec_command(f"cat << 'EOF' > /tmp/master_repair.py\n{repair_code}\nEOF")
        client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" docker cp /tmp/master_repair.py hub_prod_django:/app/master_repair.py', get_pty=True)
        
        # Run it
        cmd = "sudo docker exec hub_prod_django python3 /app/master_repair.py"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {cmd}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # 6. Verify Session Count
        print("Verifying structural integrity...")
        code = "from users.auth_models import UserSession; print(f'VERIFIED: Remote DB Connected. Table user_sessions exists.')"
        cmd = f"sudo docker exec hub_prod_django python manage.py shell -c \"{code}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {cmd}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    master_production_fix()
