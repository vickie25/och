import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()
    from django.db import connection

    with connection.cursor() as cur:
        cur.execute("ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS track_id uuid NULL;")
        cur.execute(
            "select column_name, data_type, is_nullable from information_schema.columns "
            "where table_schema='public' and table_name='cohorts' and column_name='track_id'"
        )
        print("TRACK_ID_COL", cur.fetchone())
        cur.execute("CREATE INDEX IF NOT EXISTS cohorts_track_id_idx ON cohorts(track_id);")
        print("OK index cohorts_track_id_idx")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

