import os
import sys


DDL = [
    # Core cohort fields selected by serializers/views
    "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS seat_cap integer NOT NULL DEFAULT 1;",
    "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS mentor_ratio double precision NOT NULL DEFAULT 0.1;",
    # Coordinator FK (model uses User.uuid_id). Keep nullable.
    "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS coordinator_id uuid NULL;",
    "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS calendar_id uuid NULL;",
    "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS calendar_template_id uuid NULL;",
    # JSON fields
    "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS seat_pool jsonb NOT NULL DEFAULT '{}'::jsonb;",
    # Cutoff grades (nullable decimals)
    "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS review_cutoff_grade numeric(10,2) NULL;",
    "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS interview_cutoff_grade numeric(10,2) NULL;",
    # Timestamps
    "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS created_at timestamp with time zone NOT NULL DEFAULT now();",
    "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone NOT NULL DEFAULT now();",
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
              and column_name in (
                'seat_cap','mentor_ratio','coordinator_id','calendar_id','calendar_template_id',
                'seat_pool','review_cutoff_grade','interview_cutoff_grade','created_at','updated_at'
              )
            order by column_name
            """
        )
        for row in cur.fetchall():
            print("COL", row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

