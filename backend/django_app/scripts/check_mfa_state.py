import argparse
import os
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True)
    args = ap.parse_args()

    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()

    from users.auth_models import MFACode, User
    from django.db import connection

    u = User.objects.filter(email=args.email).first()
    print("USER_EXISTS", bool(u))
    if not u:
        return 0
    print("USER_ID", u.id)
    orm_total = MFACode.objects.filter(user=u).count()
    orm_unused = MFACode.objects.filter(user=u, used=False).count()
    print("MFA_CODES_TOTAL", orm_total)
    print("MFA_CODES_UNUSED", orm_unused)

    # Raw SQL sanity check (helps when ORM/model and table drift)
    with connection.cursor() as cur:
        cur.execute("select count(*) from mfa_codes where user_id = %s", [u.id])
        sql_total = cur.fetchone()[0]
        cur.execute("select count(*) from mfa_codes where user_id = %s and used = false", [u.id])
        sql_unused = cur.fetchone()[0]
    print("MFA_CODES_SQL_TOTAL", sql_total)
    print("MFA_CODES_SQL_UNUSED", sql_unused)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

