import os
import paramiko
import sys

def surgical_create_tables():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # Surgical SQL to create ONLY the most critical tables needed for OAuth Callback
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
    "risk_score" double precision NOT NULL,
    "created_at" timestamptz NOT NULL,
    "last_activity" timestamptz NOT NULL,
    "expires_at" timestamptz NOT NULL,
    "revoked_at" timestamptz NULL,
    "user_id" bigint NOT NULL
);
CREATE INDEX IF NOT EXISTS "user_sessions_user_id_43ce9642" ON "user_sessions" ("user_id");

CREATE TABLE IF NOT EXISTS "mfa_methods" (
    "id" uuid NOT NULL PRIMARY KEY,
    "method_type" varchar(20) NOT NULL,
    "secret_encrypted" text NULL,
    "totp_backup_codes" jsonb NOT NULL,
    "phone_e164" varchar(20) NULL,
    "enabled" boolean NOT NULL,
    "is_primary" boolean NOT NULL,
    "is_verified" boolean NOT NULL,
    "verified_at" timestamptz NULL,
    "created_at" timestamptz NOT NULL,
    "last_used_at" timestamptz NULL,
    "user_id" bigint NOT NULL
);
CREATE INDEX IF NOT EXISTS "mfa_methods_user_id_5786ac34" ON "mfa_methods" ("user_id");

CREATE TABLE IF NOT EXISTS "user_identities" (
    "id" uuid NOT NULL PRIMARY KEY,
    "provider" varchar(20) NOT NULL,
    "provider_sub" varchar(255) NOT NULL,
    "metadata" jsonb NOT NULL,
    "linked_at" timestamptz NOT NULL,
    "last_sync_at" timestamptz NULL,
    "is_active" boolean NOT NULL,
    "user_id" bigint NOT NULL
);
CREATE INDEX IF NOT EXISTS "user_identi_provide_09b4c3_idx" ON "user_identities" ("provider", "provider_sub");

-- Foreign Keys (Surgical)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'user_sessions_user_id_fk') THEN
        ALTER TABLE "user_sessions" ADD CONSTRAINT "user_sessions_user_id_fk" FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY DEFERRED;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'mfa_methods_user_id_fk') THEN
        ALTER TABLE "mfa_methods" ADD CONSTRAINT "mfa_methods_user_id_fk" FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY DEFERRED;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'user_identities_user_id_fk') THEN
        ALTER TABLE "user_identities" ADD CONSTRAINT "user_identities_user_id_fk" FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY DEFERRED;
    END IF;
END $$;

-- Mark as Applied
INSERT INTO django_migrations (app, name, applied) VALUES ('users', '0001_initial', '2026-04-10 00:00:00+00') ON CONFLICT (app, name) DO NOTHING;
COMMIT;
"""
        # Execute using a temporary file to avoid shell escaping issues
        client.exec_command(f"echo '{sql}' > /tmp/surgical_fix.sql")
        command = f"sudo docker exec -i hub_prod_postgres psql -U postgres -d ongozacyberhub < /tmp/surgical_fix.sql"
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    surgical_create_tables()
