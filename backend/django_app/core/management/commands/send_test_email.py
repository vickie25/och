from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send a test email using the configured Django EMAIL_BACKEND."

    def add_arguments(self, parser):
        parser.add_argument("to", type=str, help="Recipient email address")
        parser.add_argument(
            "--subject",
            type=str,
            default="OCH Test Email",
            help="Email subject",
        )
        parser.add_argument(
            "--message",
            type=str,
            default="This is a test email from OCH.",
            help="Plain text body",
        )

    def handle(self, *args, **options):
        to_email = options["to"]
        subject = options["subject"]
        message = options["message"]

        self.stdout.write(f"EMAIL_BACKEND={getattr(settings, 'EMAIL_BACKEND', None)}")
        self.stdout.write(f"EMAIL_HOST={getattr(settings, 'EMAIL_HOST', None)}")
        self.stdout.write(f"EMAIL_PORT={getattr(settings, 'EMAIL_PORT', None)}")
        self.stdout.write(f"EMAIL_USE_SSL={getattr(settings, 'EMAIL_USE_SSL', None)}")
        self.stdout.write(f"EMAIL_USE_TLS={getattr(settings, 'EMAIL_USE_TLS', None)}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL={getattr(settings, 'DEFAULT_FROM_EMAIL', None)}")

        sent = send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[to_email],
            fail_silently=False,
        )

        if sent != 1:
            raise SystemExit(f"send_mail returned {sent}, expected 1")

        self.stdout.write(self.style.SUCCESS(f"Accepted by backend for delivery to {to_email}"))
