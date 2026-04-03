# Generated manually to fix: ProgrammingError: operator does not exist: bigint = uuid
# Some environments report users migration 0007 as applied, but the DB column
# device_trust.user_id is still bigint. This migration is idempotent and will
# convert the column to uuid (FK to users.uuid_id) if needed.

from django.db import migrations


def force_device_trust_user_id_uuid(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        # Detect current type
        cursor.execute(
            """
            SELECT data_type, udt_name
            FROM information_schema.columns
            WHERE table_name = 'device_trust' AND column_name = 'user_id'
            """
        )
        row = cursor.fetchone()
        if not row:
            return

        data_type, udt_name = row

        # Already uuid → nothing to do
        if data_type == "uuid" or udt_name == "uuid":
            return

        # Ensure users.uuid_id exists
        cursor.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'users' AND column_name = 'uuid_id'
                ) THEN
                    CREATE EXTENSION IF NOT EXISTS pgcrypto;
                    ALTER TABLE users ADD COLUMN uuid_id uuid;
                    UPDATE users SET uuid_id = gen_random_uuid() WHERE uuid_id IS NULL;
                    ALTER TABLE users ALTER COLUMN uuid_id SET NOT NULL;
                    CREATE UNIQUE INDEX IF NOT EXISTS users_uuid_id_uniq ON users(uuid_id);
                END IF;
            END $$;
            """
        )

        # Drop any existing FK constraints on device_trust.user_id
        cursor.execute(
            """
            DO $$
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (
                    SELECT conname FROM pg_constraint
                    WHERE conrelid = 'device_trust'::regclass
                    AND contype = 'f'
                    AND conname LIKE '%user_id%'
                ) LOOP
                    EXECUTE format('ALTER TABLE device_trust DROP CONSTRAINT IF EXISTS %I', r.conname);
                END LOOP;
            END $$;
            """
        )

        # Create temp uuid column
        cursor.execute("ALTER TABLE device_trust ADD COLUMN IF NOT EXISTS user_id_uuid uuid;")

        # Backfill from users.uuid_id by mapping existing bigint user_id to users.id
        cursor.execute(
            """
            UPDATE device_trust dt
            SET user_id_uuid = u.uuid_id
            FROM users u
            WHERE u.id = dt.user_id;
            """
        )

        # Swap columns
        cursor.execute("ALTER TABLE device_trust DROP COLUMN user_id;")
        cursor.execute("ALTER TABLE device_trust RENAME COLUMN user_id_uuid TO user_id;")
        cursor.execute("ALTER TABLE device_trust ALTER COLUMN user_id SET NOT NULL;")

        # Add FK to users(uuid_id)
        cursor.execute(
            """
            ALTER TABLE device_trust
            ADD CONSTRAINT device_trust_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(uuid_id) ON DELETE CASCADE;
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0011_widen_mfa_code_length"),
    ]

    operations = [
        migrations.RunPython(force_device_trust_user_id_uuid, migrations.RunPython.noop),
    ]
