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
            select column_name, data_type, udt_name
            from information_schema.columns
            where table_schema='public' and table_name='cohorts' and column_name='id'
            """
        )
        print("COHORTS_ID", cur.fetchone())

        # Find any columns named cohort_id and their types
        cur.execute(
            """
            select table_name, column_name, data_type, udt_name
            from information_schema.columns
            where table_schema='public'
              and column_name in ('cohort_id', 'assigned_cohort_id')
            order by table_name, column_name
            """
        )
        rows = cur.fetchall()
        print("COHORT_ID_COLUMNS", len(rows))
        for r in rows[:200]:
            print("COL", r)

        # FK constraints that reference cohorts(id)
        cur.execute(
            """
            select con.conname,
                   rel_t.relname as table_name,
                   att_t.attname as column_name,
                   rel_r.relname as ref_table,
                   att_r.attname as ref_column
            from pg_constraint con
            join pg_class rel_t on rel_t.oid = con.conrelid
            join pg_class rel_r on rel_r.oid = con.confrelid
            join pg_attribute att_t on att_t.attrelid = con.conrelid and att_t.attnum = con.conkey[1]
            join pg_attribute att_r on att_r.attrelid = con.confrelid and att_r.attnum = con.confkey[1]
            where con.contype='f'
              and rel_r.relname='cohorts'
              and att_r.attname='id'
            order by rel_t.relname, con.conname
            """
        )
        fks = cur.fetchall()
        print("FKS_TO_COHORTS_ID", len(fks))
        for fk in fks[:200]:
            print("FK", fk)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

