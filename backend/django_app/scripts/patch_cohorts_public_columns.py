import os
import sys


DDL = [
    # Core missing columns referenced by the public cohorts endpoint
    "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS published_to_homepage boolean NOT NULL DEFAULT false;",
    # From programs.0016_cohort_public_registration
    "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS profile_image varchar(100) NULL;",
    "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS registration_form_fields jsonb NOT NULL DEFAULT '{}'::jsonb;",
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
            print("OK", stmt)

        cur.execute(
            """
            select column_name, data_type, is_nullable
            from information_schema.columns
            where table_schema='public'
              and table_name='cohorts'
              and column_name in ('published_to_homepage','profile_image','registration_form_fields')
            order by column_name
            """
        )
        for row in cur.fetchall():
            print("COL", row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

