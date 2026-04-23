import argparse
import os
import sys
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc)


def _ensure_username(User, email: str) -> str:
    base = (email.split("@", 1)[0] or "user").strip()[:120]
    cand = base
    i = 0
    while User.objects.filter(username=cand).exists():
        i += 1
        cand = f"{base}{i}"
        if len(cand) > 150:
            cand = cand[:150]
    return cand


def _assign_role(Role, UserRole, user, role_name: str) -> None:
    role, _ = Role.objects.get_or_create(name=role_name)
    # scope_ref is a UUIDField; keep it NULL for global roles.
    UserRole.objects.update_or_create(
        user=user,
        role=role,
        scope="global",
        scope_ref=None,
        defaults={"is_active": True},
    )


def _disable_mfa(MFAMethod, MFACode, user) -> None:
    # Clear any enrolled methods/codes so login doesn't prompt MFA.
    try:
        MFAMethod.objects.filter(user=user).delete()
    except Exception:
        # DB restores can miss this table; disabling mfa_enabled is still effective.
        pass
    try:
        MFACode.objects.filter(user=user).delete()
    except Exception:
        pass
    user.mfa_enabled = False
    user.mfa_method = None


def _verify_and_activate(user) -> None:
    user.is_active = True
    user.account_status = "active"
    user.email_verified = True
    now = _now()
    user.email_verified_at = now
    if not user.activated_at:
        user.activated_at = now


def main() -> int:
    ap = argparse.ArgumentParser(description="Provision privileged users (admin/director) safely.")
    ap.add_argument("--admin-email", required=True)
    ap.add_argument("--admin-password", required=True)
    ap.add_argument("--admin-first-name", default="Kelvin")
    ap.add_argument("--admin-last-name", default="Maina")
    ap.add_argument("--director-email", required=True)
    ap.add_argument("--director-password", default="")
    ap.add_argument("--director-first-name", default="Program")
    ap.add_argument("--director-last-name", default="Director")
    args = ap.parse_args()

    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()

    from users.auth_models import MFACode, MFAMethod
    from users.models import Role, User, UserRole

    admin_email = args.admin_email.strip().lower()
    director_email = args.director_email.strip().lower()

    # Admin user
    admin = User.objects.filter(email__iexact=admin_email).first()
    created_admin = False
    if not admin:
        created_admin = True
        admin = User.objects.create_user(
            email=admin_email,
            username=_ensure_username(User, admin_email),
            password=args.admin_password,
        )
    else:
        admin.set_password(args.admin_password)

    admin.first_name = args.admin_first_name
    admin.last_name = args.admin_last_name
    admin.is_staff = True
    admin.is_superuser = True
    _verify_and_activate(admin)
    _disable_mfa(MFAMethod, MFACode, admin)
    admin.save()
    _assign_role(Role, UserRole, admin, "admin")

    # Director user
    director_pw = (args.director_password or "").strip() or args.admin_password
    director = User.objects.filter(email__iexact=director_email).first()
    created_director = False
    if not director:
        created_director = True
        director = User.objects.create_user(
            email=director_email,
            username=_ensure_username(User, director_email),
            password=director_pw,
        )
    else:
        director.set_password(director_pw)

    director.first_name = args.director_first_name
    director.last_name = args.director_last_name
    director.is_staff = True  # director surfaces are staff-like internally
    director.is_superuser = False
    _verify_and_activate(director)
    _disable_mfa(MFAMethod, MFACode, director)
    director.save()
    _assign_role(Role, UserRole, director, "program_director")

    print("OK")
    print("ADMIN_EMAIL", admin.email, "CREATED" if created_admin else "UPDATED")
    print("DIRECTOR_EMAIL", director.email, "CREATED" if created_director else "UPDATED")
    print("NOTE", "Director password set (defaults to admin password if not provided).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

