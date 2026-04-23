import argparse
import os
import sys


def main() -> int:
    ap = argparse.ArgumentParser(description="Trigger an email MFA OTP for a user (server-side).")
    ap.add_argument("--email", required=True)
    ap.add_argument("--expires-minutes", type=int, default=10)
    args = ap.parse_args()

    sys.path.insert(0, "/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    import django

    django.setup()

    from django.conf import settings
    from django.core.mail import send_mail
    from users.auth_models import User
    from users.utils.auth_utils import create_mfa_code

    email = args.email.strip().lower()
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        print("USER_NOT_FOUND")
        return 4

    code, _ = create_mfa_code(user, method="email", expires_minutes=args.expires_minutes)

    subject = "OCH MFA Code"
    message = (
        f"Your OCH verification code is: {code}\n\n"
        f"This code expires in {args.expires_minutes} minutes.\n"
        f"If you did not request this, you can ignore this email."
    )

    sent = send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email],
        fail_silently=False,
    )
    print("SENT", sent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

