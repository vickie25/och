import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()

    from django.db import connection

    print("SMOKE_PHASE3_FINANCE")

    must_have_tables = [
        "wallets",
        "transactions",
        "credits",
        "contracts",
        "invoices",
        "payments",
        "pricing_tiers",
    ]
    with connection.cursor() as cur:
        for t in must_have_tables:
            cur.execute("select to_regclass(%s)", [f"public.{t}"])
            print("TABLE", t, "OK" if cur.fetchone()[0] else "MISSING")

    # Minimal HTTP smoke (direct to Django inside container)
    try:
        import requests

        def hit(path: str):
            url = f"http://127.0.0.1:8000{path}"
            r = requests.get(url, timeout=20)
            body = (r.text or "")[:200].replace("\n", " ")
            print("HTTP", path, r.status_code, body)
            return r.status_code

        hit("/api/v1/health/")
        # Finance endpoints are mostly auth-protected; we just ensure the service responds (401 is OK).
        hit("/api/v1/finance/health/")  # if exists; otherwise likely 404
        hit("/api/v1/subscriptions/plans/")  # typically public; may be 200/404 depending on app
    except Exception as e:
        print("HTTP_SMOKE_ERROR", type(e).__name__, str(e))
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

