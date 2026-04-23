import os
import sys


DDL = [
    'CREATE EXTENSION IF NOT EXISTS "pgcrypto";',
    # Add uuid_id if missing; keep nullable initially to allow fast add on large tables.
    "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS uuid_id uuid NULL;",
    # Backfill any NULL uuid_id (fast enough for typical cohort counts)
    "UPDATE cohorts SET uuid_id = gen_random_uuid() WHERE uuid_id IS NULL;",
    # Make it NOT NULL (after backfill)
    "ALTER TABLE cohorts ALTER COLUMN uuid_id SET NOT NULL;",
    # Unique index so we can safely reference it
    "CREATE UNIQUE INDEX IF NOT EXISTS cohorts_uuid_id_uniq ON cohorts(uuid_id);",
]


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()
    from django.db import connection

    with connection.cursor() as cur:
        for stmt in DDL:
            cur.execute(stmt)
            print("OK", stmt.splitlines()[0].strip()[:100])

        cur.execute(
            """
            select
              (select count(*) from cohorts) as total,
              (select count(*) from cohorts where uuid_id is null) as null_uuid_id
            """
        )
        print("COHORTS_COUNTS", cur.fetchone())

        cur.execute(
            """
            select column_name, data_type, is_nullable
            from information_schema.columns
            where table_schema='public' and table_name='cohorts' and column_name='uuid_id'
            """
        )
        print("UUID_ID_COL", cur.fetchone())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

