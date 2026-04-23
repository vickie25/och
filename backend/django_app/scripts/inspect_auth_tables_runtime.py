import os
import sys


TABLES = [
    "mfa_methods",
    "mfa_codes",
    "user_sessions",
    "device_trust",
    "audit_logs",
    "consent_scopes",
    "entitlements",
]


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()
    from django.db import connection

    with connection.cursor() as cur:
        for t in TABLES:
            cur.execute("select to_regclass(%s)", [f"public.{t}"])
            print(t, cur.fetchone()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

