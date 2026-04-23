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
            """
            select c.relkind, c.relname, n.nspname
            from pg_class c
            join pg_namespace n on n.oid = c.relnamespace
            where n.nspname='public' and c.relname='cohorts'
            """
        )
        print("PG_CLASS", cur.fetchone())

        cur.execute(
            """
            select table_type
            from information_schema.tables
            where table_schema='public' and table_name='cohorts'
            """
        )
        print("INFO_SCHEMA_TABLE_TYPE", cur.fetchone())

        cur.execute(
            """
            select column_name, data_type
            from information_schema.columns
            where table_schema='public' and table_name='cohorts' and column_name='mode'
            """
        )
        print("MODE_COLUMN", cur.fetchone())

        cur.execute(
            """
            select column_name
            from information_schema.columns
            where table_schema='public' and table_name='cohorts'
            order by ordinal_position
            """
        )
        cols = [r[0] for r in cur.fetchall()]
        print("COLS_COUNT", len(cols))
        print("COLS_HAS_MODE", "mode" in cols)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

