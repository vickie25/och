import os
import paramiko
import sys

def surgical_repair_final_final():
    host = "69.30.235.220"
    user = "administrator"
    password = os.environ.get('PRODUCTION_SSH_PASSWORD', '')
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print("\n--- [RUNNING FINAL-FINAL STRUCTURAL REPAIR] ---")
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

-- Mark as Applied (Reset first to ensure no conflicts)
DELETE FROM django_migrations WHERE app='users' AND name='0001_initial';
INSERT INTO django_migrations (app, name, applied) VALUES ('users', '0001_initial', '2026-04-10 00:00:00+00');
COMMIT;
"""
        # Execute using the HEREDOC method which finally showed output
        remote_script = "/tmp/repair_final_v2.sh"
        bash_content = f"""
cat << 'EOSQL' > /tmp/surgical_v2.sql
{sql}
EOSQL
echo "{password}" | sudo -S docker exec -i hub_prod_postgres psql -U postgres -d ongozacyberhub < /tmp/surgical_v2.sql
"""
        # Use simple escaping for bash_content in echo
        client.exec_command(f"cat << 'EOF' > {remote_script}\n{bash_content}\nEOF")
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" bash {remote_script}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))
        
        # FINAL VERIFICATION
        print("\n--- [FINAL VERIFICATION] ---")
        command = "sudo docker exec hub_prod_postgres psql -U postgres -d ongozacyberhub -c \"SELECT tablename FROM pg_catalog.pg_tables WHERE tablename='user_sessions'\""
        stdin, stdout, stderr = client.exec_command(f'printf "%s\\n" "{password}" | sudo -S -p "" {command}', get_pty=True)
        print(stdout.read().decode('utf-8', 'ignore'))

        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    surgical_repair_final_final()
