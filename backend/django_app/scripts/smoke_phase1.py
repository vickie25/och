import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()

    from django.db import connection

    print("SMOKE_PHASE1")

    # DB assertions (tables exist)
    must_have_tables = [
        "users",
        "cohorts",
        "tracks",
        "curriculum_tracks",
        "ai_coach_sessions",
        "profilersessions",
        "django_migrations",
    ]
    with connection.cursor() as cur:
        for t in must_have_tables:
            cur.execute("select to_regclass(%s)", [f"public.{t}"])
            reg = cur.fetchone()[0]
            print("TABLE", t, "OK" if reg else "MISSING")

    # Minimal HTTP smoke (through nginx inside Docker network)
    try:
        import requests

        def hit(path: str, params: dict | None = None):
            # On this VPS compose, Django is the edge API (no nginx container).
            # Hit the local gunicorn port directly from inside the container.
            url = f"http://127.0.0.1:8000{path}"
            r = requests.get(url, params=params, timeout=20)
            body = (r.text or "")[:180].replace("\n", " ")
            print("HTTP", path, r.status_code, body)
            return r.status_code

        hit("/api/v1/health/")
        hit("/api/v1/auth/google/initiate", params={"role": "student", "mode": "login"})
        hit("/api/v1/public/cohorts/")
    except Exception as e:
        print("HTTP_SMOKE_ERROR", type(e).__name__, str(e))
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

