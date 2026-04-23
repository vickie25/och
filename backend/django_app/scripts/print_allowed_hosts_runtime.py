import os
import sys
from pathlib import Path


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()

    from django.conf import settings

    print("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE"))
    print("ENV_ALLOWED_HOSTS", os.environ.get("ALLOWED_HOSTS", "<missing>"))
    print("SETTINGS_ALLOWED_HOSTS", getattr(settings, "ALLOWED_HOSTS", None))

    p = Path("/app/core/settings/production.py")
    if p.exists():
        txt = p.read_text(encoding="utf-8", errors="replace")
        print("PRODUCTION_PY_HAS_BACKEND", ("'backend'" in txt) or ('"backend"' in txt))
    else:
        print("PRODUCTION_PY_MISSING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

