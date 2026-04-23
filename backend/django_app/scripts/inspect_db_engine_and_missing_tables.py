import os
import sys


TABLES = [
    # errors reported by UI
    "profilersessions",
    "curriculum_tracks",
    "ai_coach_sessions",
    # sanity checks
    "django_migrations",
    "users",
    "cohorts",
]


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()

    from django.db import connection

    print("DB_VENDOR", connection.vendor)
    for k in ("ENGINE", "NAME", "HOST", "PORT", "USER"):
        v = connection.settings_dict.get(k)
        if k == "USER" and v:
            # Not a secret, but avoid dumping identifiers in logs.
            v = "<set>"
        print(f"DB_{k}", v)

    with connection.cursor() as cur:
        cur.execute("select current_database(), current_schema(), current_setting('search_path')")
        db, schema, search_path = cur.fetchone()
        print("DB_CURRENT_DATABASE", db)
        print("DB_CURRENT_SCHEMA", schema)
        print("DB_SEARCH_PATH", search_path)

        print("TABLE_REGCLASS")
        for t in TABLES:
            cur.execute("select to_regclass(%s)", [f"public.{t}"])
            print(t, cur.fetchone()[0])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

