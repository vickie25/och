import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()
    from django.db import connection

    with connection.cursor() as cur:
        cur.execute("select to_regclass('public.entitlements')")
        print("ENTITLEMENTS_REGCLASS", cur.fetchone()[0])

        cur.execute(
            """
            select column_name
            from information_schema.columns
            where table_schema='public' and table_name='cohorts' and column_name='status'
            """
        )
        print("COHORTS_HAS_STATUS", bool(cur.fetchone()))

        cur.execute(
            """
            select column_name
            from information_schema.columns
            where table_schema='public' and table_name='cohorts' and column_name='published_to_homepage'
            """
        )
        print("COHORTS_HAS_PUBLISHED", bool(cur.fetchone()))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

