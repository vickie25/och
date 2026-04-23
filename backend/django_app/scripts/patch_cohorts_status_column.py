import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()
    from django.db import connection

    with connection.cursor() as cur:
        # Minimal column needed for filters in public cohort listing
        cur.execute(
            "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS status varchar(24) NOT NULL DEFAULT 'draft';"
        )
        cur.execute(
            "select column_name, data_type, is_nullable, column_default from information_schema.columns "
            "where table_schema='public' and table_name='cohorts' and column_name='status'"
        )
        print("STATUS_COL", cur.fetchone())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

