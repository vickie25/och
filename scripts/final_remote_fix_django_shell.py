import paramiko
import sys

def final_remote_fix_django_shell():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [FORCING REMOTE DB STRUCTURAL REPAIR VIA DJANGO SHELL] ---")
        
        # We use a heredoc to pass the complex python code to the container
        python_repair_code = """
import os
import django
from django.db import connection, transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

print(f"TARGET DB HOST: {os.environ.get('DB_HOST')}")

def run_sql(sql):
    with connection.cursor() as cursor:
        try:
            cursor.execute(sql)
            print(f"SUCCESS: {sql[:50]}...")
            transaction.commit()
        except Exception as e:
            if 'already exists' in str(e):
                print(f"SKIPPED: {sql[:50]}... (Already exists)")
            else:
                print(f"ERROR on {sql[:30]}: {str(e)}")

queries = [
    'CREATE TABLE "user_sessions" ("id" uuid NOT NULL PRIMARY KEY, "device_fingerprint" varchar(255) NOT NULL, "device_name" varchar(255) NULL, "device_type" varchar(50) NULL, "ip_address" inet NULL, "ua" text NULL, "refresh_token_hash" varchar(64) NOT NULL UNIQUE, "is_trusted" boolean NOT NULL, "trusted_at" timestamptz NULL, "mfa_verified" boolean NOT NULL, "risk_score" double precision NOT NULL, "created_at" timestamptz NOT NULL, "last_activity" timestamptz NOT NULL, "expires_at" timestamptz NOT NULL, "revoked_at" timestamptz NULL, "user_id" bigint NOT NULL)',
    'CREATE INDEX "user_sessions_user_id_idx" ON "user_sessions" ("user_id")',
    'CREATE TABLE "mfa_methods" ("id" uuid NOT NULL PRIMARY KEY, "method_type" varchar(20) NOT NULL, "secret_encrypted" text NULL, "totp_backup_codes" jsonb NOT NULL, "phone_e164" varchar(20) NULL, "enabled" boolean NOT NULL, "is_primary" boolean NOT NULL, "is_verified" boolean NOT NULL, "verified_at" timestamptz NULL, "created_at" timestamptz NOT NULL, "last_used_at" timestamptz NULL, "user_id" bigint NOT NULL)',
    'CREATE INDEX "mfa_methods_user_id_idx" ON "mfa_methods" ("user_id")',
    'CREATE TABLE "user_identities" ("id" uuid NOT NULL PRIMARY KEY, "provider" varchar(20) NOT NULL, "provider_sub" varchar(255) NOT NULL, "metadata" jsonb NOT NULL, "linked_at" timestamptz NOT NULL, "last_sync_at" timestamptz NULL, "is_active" boolean NOT NULL, "user_id" bigint NOT NULL)',
    'CREATE INDEX "user_ident_provide_idx" ON "user_identities" ("provider", "provider_sub")',
    "DELETE FROM django_migrations WHERE app='users' AND name='0001_initial'",
    "INSERT INTO django_migrations (app, name, applied) VALUES ('users', '0001_initial', '2026-04-10 00:00:00+00')"
]

for q in queries:
    run_sql(q)

print("Migration Sync Complete.")
"""
        # Save logic to remote temp file
        logic_file = "/tmp/final_repair_logic.py"
        client.exec_command(f"cat << 'EOF' > {logic_file}\n{python_repair_code}\nEOF")
        
        # Execute logic inside container via piping to python
        command = f"sudo docker exec -i hub_prod_django python3 -"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        
        stdin.write(python_repair_code)
        stdin.close()
        
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    final_remote_fix_django_shell()
