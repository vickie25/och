import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()
    from django.db import connection

    with connection.cursor() as cur:
        cur.execute("show search_path")
        print("SEARCH_PATH", cur.fetchone()[0])

        # Find any table named cohorts across schemas
        cur.execute(
            """
            select n.nspname as schema_name, c.relname as table_name
            from pg_class c
            join pg_namespace n on n.oid = c.relnamespace
            where c.relkind = 'r' and c.relname = 'cohorts'
            order by n.nspname
            """
        )
        rows = cur.fetchall()
        print("COHORTS_TABLES", len(rows))
        for schema_name, table_name in rows:
            cur.execute(
                """
                select column_name
                from information_schema.columns
                where table_schema = %s and table_name = %s and column_name = 'published_to_homepage'
                """,
                [schema_name, table_name],
            )
            has_col = bool(cur.fetchone())
            print("TABLE", f"{schema_name}.{table_name}", "HAS_published_to_homepage", has_col)

        # Sanity check: which table does an unqualified SELECT hit?
        try:
            cur.execute("select count(*) from cohorts")
            print("UNQUALIFIED_SELECT_OK", cur.fetchone()[0])
            cur.execute(
                """
                select exists(
                  select 1
                  from information_schema.columns
                  where table_schema = split_part(current_schema(),'.',1)
                )
                """
            )
        except Exception as e:
            print("UNQUALIFIED_SELECT_FAIL", type(e).__name__, str(e))

        # Check column in public.cohorts explicitly
        cur.execute(
            """
            select column_name, data_type, is_nullable
            from information_schema.columns
            where table_schema='public' and table_name='cohorts'
              and column_name in ('published_to_homepage','profile_image','registration_form_fields')
            order by column_name
            """
        )
        for row in cur.fetchall():
            print("PUBLIC_COL", row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

