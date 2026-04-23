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
            "ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS curriculum_tracks jsonb NOT NULL DEFAULT '[]'::jsonb;"
        )
        cur.execute(
            "select column_name, data_type, is_nullable, column_default "
            "from information_schema.columns "
            "where table_schema='public' and table_name='cohorts' and column_name='curriculum_tracks'"
        )
        print("CURRICULUM_TRACKS_COL", cur.fetchone())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

