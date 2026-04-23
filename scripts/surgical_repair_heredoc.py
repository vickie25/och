import os
import paramiko
import sys

def surgical_repair_heredoc():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [RUNNING SURGICAL REPAIR VIA HEREDOC] ---")
        # Use a remote script to run the psql with heredoc
        remote_script = "/tmp/repair_final.sh"
        bash_content = f"""
cat << 'EOSQL' > /tmp/surgical.sql
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
INSERT INTO django_migrations (app, name, applied) VALUES ('users', '0001_initial', '2026-04-10 00:00:00+00') ON CONFLICT (app, name) DO NOTHING;
COMMIT;
EOSQL
echo "{password}" | sudo -S docker exec -i hub_prod_postgres psql -U postgres -d ongozacyberhub < /tmp/surgical.sql
"""
        client.exec_command(f"echo \"{bash_content}\" > {remote_script}")
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" bash {remote_script}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # Second command: Final verification
        print("\n--- [FINAL VERIFICATION] ---")
        command = "sudo docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"SELECT tablename FROM pg_catalog.pg_tables WHERE tablename='user_sessions'\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    surgical_repair_heredoc()
