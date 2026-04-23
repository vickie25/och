import os
import sys


def main() -> int:
    email = os.environ.get("EMAIL", "kelvin2o2maina@gmail.com")
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")

    import django

    django.setup()

    from users.models import User
    from rest_framework_simplejwt.tokens import RefreshToken

    u = User.objects.filter(email__iexact=email).first()
    if not u:
        print("USER_NOT_FOUND", email)
        return 2

    t = RefreshToken.for_user(u)
    print(str(t.access_token))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

