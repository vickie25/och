import os
import paramiko
import sys

def remote_surgical_repair():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    remote_db_host = "38.247.138.250"
    
    sql = """
BEGIN;
CREATE TABLE IF NOT EXISTS "user_sessions" (
    "id" uuid NOT NULL PRIMARY KEY,
    "device_fingerprint" varchar(255) NOT NULL,
    "device_name" varchar(255) NULL,
    "device_type" varchar(50) NULL,
    "ip_address" inet NULL,
    "ua" text NULL,
    "refresh_token_hash" varchar(64) NOT NULL UNIQUE,
    "is_trusted" boolean NOT NULL,
    "trusted_at" timestamptz NULL,
    "mfa_verified" boolean NOT NULL,
    "risk_score" double precision NOT NULL, "created_at" timestamptz NOT NULL, "last_activity" timestamptz NOT NULL, "expires_at" timestamptz NOT NULL, "revoked_at" timestamptz NULL, "user_id" bigint NOT NULL
);
CREATE INDEX IF NOT EXISTS "user_sessions_user_id_idx" ON "user_sessions" ("user_id");

CREATE TABLE IF NOT EXISTS "mfa_methods" (
    "id" uuid NOT NULL PRIMARY KEY, "method_type" varchar(20) NOT NULL, "secret_encrypted" text NULL, "totp_backup_codes" jsonb NOT NULL, "phone_e164" varchar(20) NULL, "enabled" boolean NOT NULL, "is_primary" boolean NOT NULL, "is_verified" boolean NOT NULL, "verified_at" timestamptz NULL, "created_at" timestamptz NOT NULL, "last_used_at" timestamptz NULL, "user_id" bigint NOT NULL
);
CREATE INDEX IF NOT EXISTS "mfa_methods_user_id_idx" ON "mfa_methods" ("user_id");

CREATE TABLE IF NOT EXISTS "user_identities" (
    "id" uuid NOT NULL PRIMARY KEY, "provider" varchar(20) NOT NULL, "provider_sub" varchar(255) NOT NULL, "metadata" jsonb NOT NULL, "linked_at" timestamptz NOT NULL, "last_sync_at" timestamptz NULL, "is_active" boolean NOT NULL, "user_id" bigint NOT NULL
);
CREATE INDEX IF NOT EXISTS "user_ident_provide_idx" ON "user_identities" ("provider", "provider_sub");

-- Record the migration
DELETE FROM django_migrations WHERE app='users' AND name='0001_initial';
INSERT INTO django_migrations (app, name, applied) VALUES ('users', '0001_initial', NOW());
COMMIT;
"""

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print(f"\n--- [RUNNING SURGICAL REPAIR ON REMOTE DB: {remote_db_host}] ---")
        
        # We use a temporary SQL file on the host to avoid piping issues
        client.exec_command(f"echo \"{sql}\" > /tmp/remote_repair.sql")
        
        # Execute psql from the host pointing to the remote DB
        command = f"PGPASSWORD=postgres psql -h {remote_db_host} -U postgres -d ongozacyberhub < /tmp/remote_repair.sql"
        stdin, stdout, stderr = client.exec_command(command)
        
        print(f"STDOUT: {stdout.read().decode('utf-8', 'ignore')}")
        print(f"STDERR: {stderr.read().decode('utf-8', 'ignore')}")
        
        # FINAL STEP: Ensure Django can connects
        print("\n--- [VERIFYING REMOTE CONNECTION VIA DJANGO] ---")
        code = "from users.auth_models import UserSession; print(f'REMOTE VERIFIED: Count={UserSession.objects.count()}')"
        command = f"sudo docker exec hub_prod_django python manage.py shell -c \"{code}\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    remote_surgical_repair()
