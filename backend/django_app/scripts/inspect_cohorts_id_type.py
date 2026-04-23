import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()
    from django.db import connection

    with connection.cursor() as cur:
        cur.execute(
            "select column_name, data_type, udt_name "
            "from information_schema.columns "
            "where table_schema='public' and table_name='cohorts' and column_name='id'"
        )
        print("COHORTS_ID_COL", cur.fetchone())
        cur.execute("select pg_typeof(id)::text from cohorts limit 1")
        row = cur.fetchone()
        print("COHORTS_ID_PGTYPE", row[0] if row else "<empty>")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

