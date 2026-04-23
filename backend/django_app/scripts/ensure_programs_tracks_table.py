import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()
    from django.db import connection

    ddl = """
    CREATE TABLE IF NOT EXISTS "tracks" (
      "id" uuid NOT NULL PRIMARY KEY,
      "program_id" uuid NULL,
      "name" varchar(200) NOT NULL,
      "key" varchar(100) NOT NULL,
      "track_type" varchar(20) NULL,
      "description" text NOT NULL DEFAULT '',
      "competencies" jsonb NOT NULL DEFAULT '{}'::jsonb,
      "missions" jsonb NOT NULL DEFAULT '[]'::jsonb,
      "director_id" uuid NULL,
      "created_at" timestamp with time zone NOT NULL DEFAULT now(),
      "updated_at" timestamp with time zone NOT NULL DEFAULT now()
    );
    """

    with connection.cursor() as cur:
        cur.execute(ddl)
        cur.execute("select to_regclass('public.tracks')")
        print("TRACKS_REGCLASS", cur.fetchone()[0])
        cur.execute(
            "select column_name from information_schema.columns where table_schema='public' and table_name='tracks' order by ordinal_position"
        )
        cols = [r[0] for r in cur.fetchall()]
        print("TRACKS_COLS", cols)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

