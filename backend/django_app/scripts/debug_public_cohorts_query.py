import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()

    from programs.models import Cohort
    from django.db import connection

    print("DB_TABLE", Cohort._meta.db_table)
    with connection.cursor() as cur:
        cur.execute("select current_database(), current_schema(), current_setting('search_path')")
        db, schema, search_path = cur.fetchone()
        print("DB", db)
        print("SCHEMA", schema)
        print("SEARCH_PATH", search_path)

        cur.execute("select to_regclass('public.cohorts')")
        print("REGCLASS", cur.fetchone()[0])
        cur.execute("select to_regclass('cohorts')")
        print("REGCLASS_UNQUALIFIED", cur.fetchone()[0])

        # Show where "cohorts" exists and whether it has track_id.
        cur.execute(
            """
            select table_schema, table_type
            from information_schema.tables
            where table_name='cohorts'
            order by table_schema
            """
        )
        rows = cur.fetchall()
        print("COHORTS_TABLES", rows)

        cur.execute(
            """
            select table_schema, column_name, data_type, is_nullable
            from information_schema.columns
            where table_name='cohorts' and column_name in ('status','published_to_homepage','track_id')
            order by table_schema, column_name
            """
        )
        print("COHORTS_KEY_COLS", cur.fetchall())

        cur.execute(
            "select column_name from information_schema.columns where table_schema='public' and table_name='cohorts' and column_name='status'"
        )
        print("HAS_STATUS", bool(cur.fetchone()))

    qs = (
        Cohort.objects.filter(published_to_homepage=True, status__in=["draft", "active", "running"])
        .select_related("track")
        .order_by("start_date")
    )
    try:
        # Print SQL before evaluation so we can diagnose DB-level errors.
        print("SQL", str(qs.query)[:900])
        print("COUNT", qs.count())
        # Force queryset evaluation (will surface missing joined tables/columns even when result is empty)
        rows = list(qs[:1])
        print("EVAL_OK", len(rows))
    except Exception as e:
        import traceback

        print("QUERY_FAIL", type(e).__name__, str(e))
        print(traceback.format_exc())
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

