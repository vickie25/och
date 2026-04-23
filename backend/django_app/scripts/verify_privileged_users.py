import os
import sys


def main() -> int:
    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()

    from users.models import User, UserRole

    emails = [
        "kelvinmaina202@gmail.com",
        "mystaurtupkenya@gmail.com",
    ]

    for email in emails:
        u = User.objects.filter(email__iexact=email).first()
        print("USER", email, "EXISTS" if u else "MISSING")
        if not u:
            continue
        print(
            "FLAGS",
            "is_active",
            u.is_active,
            "is_staff",
            u.is_staff,
            "is_superuser",
            u.is_superuser,
            "email_verified",
            u.email_verified,
            "account_status",
            u.account_status,
            "mfa_enabled",
            u.mfa_enabled,
        )
        roles = list(
            UserRole.objects.filter(user=u, is_active=True)
            .select_related("role")
            .values_list("role__name", flat=True)
        )
        print("ROLES", roles)
        print("---")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

