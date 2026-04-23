import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()
    from django.db import connection

    with connection.cursor() as cur:
        # Django model expects Cohort.mode; DB restore drift can omit it.
        cur.execute("ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS mode varchar(20) NOT NULL DEFAULT 'virtual';")
        cur.execute(
            "select column_name, data_type, is_nullable, column_default "
            "from information_schema.columns "
            "where table_schema='public' and table_name='cohorts' and column_name='mode'"
        )
        print("MODE_COL", cur.fetchone())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()
    from django.db import connection

    with connection.cursor() as cur:
        cur.execute("ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS mode varchar(20) NOT NULL DEFAULT 'virtual';")
        cur.execute(
            "select column_name, data_type, is_nullable, column_default "
            "from information_schema.columns "
            "where table_schema='public' and table_name='cohorts' and column_name='mode'"
        )
        print("MODE_COL", cur.fetchone())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

