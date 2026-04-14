"""
Certificate Notification Service
Automated email notifications for certificate renewal per OCH Certificate Renewal Model v1.0
"""
import logging
from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class CertificateNotificationService:
    """
    Service for sending automated certificate renewal notifications.

    Notification Schedule:
    - 60 days before expiry: "Your OCH {Track} Certificate renews soon"
    - 30 days before expiry: "Action needed: Renew your OCH {Track} Certificate"
    - 7 days before expiry: "Urgent: Your OCH {Track} Certificate expires in 7 days"
    - On expiry date: "Your OCH {Track} Certificate has entered grace period"
    - Grace period end: "Your OCH {Track} Certificate has expired"
    """

    NOTIFICATION_TRIGGERS = [
        (60, '60_day_reminder'),
        (30, '30_day_reminder'),
        (7, '7_day_reminder'),
    ]

    @staticmethod
    def check_and_send_notifications():
        """
        Check all certificates and send appropriate notifications.
        This method should be run daily via cron or celery beat.
        """
        today = date.today()

        # Process renewal notifications
        CertificateNotificationService._process_renewal_notifications(today)

        # Process grace period notifications
        CertificateNotificationService._process_grace_period_notifications(today)

        # Process expired notifications
        CertificateNotificationService._process_expired_notifications(today)

    @staticmethod
    def _process_renewal_notifications(today):
        """Send renewal reminder notifications."""
        from .models import Certificate

        for days_before, trigger_name in CertificateNotificationService.NOTIFICATION_TRIGGERS:
            target_date = today + timedelta(days=days_before)

            # Find certificates expiring on target date that haven't been notified
            certificates = Certificate.objects.filter(
                expiry_date=target_date,
                status='active',
                next_notification_date__isnull=True
            )

            for cert in certificates:
                try:
                    CertificateNotificationService.send_renewal_notification(cert, days_before)

                    # Update next notification date
                    if days_before == 60:
                        cert.next_notification_date = cert.expiry_date - timedelta(days=30)
                    elif days_before == 30:
                        cert.next_notification_date = cert.expiry_date - timedelta(days=7)
                    elif days_before == 7:
                        cert.next_notification_date = cert.expiry_date

                    cert.save(update_fields=['next_notification_date'])

                except Exception as e:
                    logger.error(f"Failed to send {trigger_name} for certificate {cert.id}: {e}")

    @staticmethod
    def _process_grace_period_notifications(today):
        """Send grace period entry notifications."""
        from .models import Certificate

        # Find certificates that just entered grace period
        certificates = Certificate.objects.filter(
            expiry_date=today,
            status='active'
        )

        for cert in certificates:
            try:
                # Update status to grace period
                cert.status = 'grace_period'
                cert.save(update_fields=['status'])

                # Send notification
                CertificateNotificationService.send_grace_period_notification(cert)

                # Set next notification for grace period end
                cert.next_notification_date = cert.grace_period_end
                cert.save(update_fields=['next_notification_date'])

            except Exception as e:
                logger.error(f"Failed to process grace period for certificate {cert.id}: {e}")

    @staticmethod
    def _process_expired_notifications(today):
        """Send expiration notifications."""
        from .models import Certificate

        # Find certificates whose grace period ended today
        certificates = Certificate.objects.filter(
            grace_period_end=today,
            status='grace_period'
        )

        for cert in certificates:
            try:
                # Update status to expired
                cert.status = 'expired'
                cert.save(update_fields=['status'])

                # Send notification
                CertificateNotificationService.send_expiration_notification(cert)

            except Exception as e:
                logger.error(f"Failed to process expiration for certificate {cert.id}: {e}")

    @staticmethod
    def send_renewal_notification(certificate, days_remaining):
        """
        Send renewal reminder email.

        Args:
            certificate: Certificate instance
            days_remaining: Number of days until expiry
        """
        user = certificate.enrollment.user
        track = certificate.enrollment.cohort.track

        # Determine email content based on days remaining
        if days_remaining == 60:
            subject = f"Your OCH {track.name} Certificate renews soon"
            template = 'certificates/emails/60_day_reminder.html'
        elif days_remaining == 30:
            subject = f"Action needed: Renew your OCH {track.name} Certificate"
            template = 'certificates/emails/30_day_reminder.html'
        elif days_remaining == 7:
            subject = f"Urgent: Your OCH {track.name} Certificate expires in 7 days"
            template = 'certificates/emails/7_day_reminder.html'
        else:
            return

        # Build context
        context = {
            'student_name': user.first_name or user.email,
            'track_name': track.name,
            'certificate_id': certificate.certificate_id_formatted,
            'expiry_date': certificate.expiry_date,
            'days_remaining': days_remaining,
            'renewal_url': f"{settings.FRONTEND_URL}/certificates/{certificate.id}/renew",
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
        }

        # Send email
        html_message = render_to_string(template, context)
        plain_message = f"""
        Hi {context['student_name']},

        Your OCH {track.name} Certificate (ID: {certificate.certificate_id_formatted})
        expires on {certificate.expiry_date} ({days_remaining} days remaining).

        Please renew your certificate to maintain your credentials.

        Renew here: {context['renewal_url']}

        Best regards,
        Ongoza Cyber Hub Team
        """

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )

        logger.info(f"Sent {days_remaining}-day renewal notification to {user.email} for cert {certificate.id}")

    @staticmethod
    def send_grace_period_notification(certificate):
        """Send grace period entry notification."""
        user = certificate.enrollment.user
        track = certificate.enrollment.cohort.track

        subject = f"Your OCH {track.name} Certificate has entered grace period"

        context = {
            'student_name': user.first_name or user.email,
            'track_name': track.name,
            'certificate_id': certificate.certificate_id_formatted,
            'grace_period_end': certificate.grace_period_end,
            'renewal_url': f"{settings.FRONTEND_URL}/certificates/{certificate.id}/renew",
        }

        html_message = render_to_string('certificates/emails/grace_period.html', context)
        plain_message = f"""
        Hi {context['student_name']},

        Your OCH {track.name} Certificate (ID: {certificate.certificate_id_formatted})
        has expired and entered a 30-day grace period.

        You have until {certificate.grace_period_end} to renew your certificate
        before it is permanently marked as expired.

        Renew now: {context['renewal_url']}

        Best regards,
        Ongoza Cyber Hub Team
        """

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )

        logger.info(f"Sent grace period notification to {user.email} for cert {certificate.id}")

    @staticmethod
    def send_expiration_notification(certificate):
        """Send final expiration notification."""
        user = certificate.enrollment.user
        track = certificate.enrollment.cohort.track

        subject = f"Your OCH {track.name} Certificate has expired"

        context = {
            'student_name': user.first_name or user.email,
            'track_name': track.name,
            'certificate_id': certificate.certificate_id_formatted,
            'recertification_url': f"{settings.FRONTEND_URL}/programs/{track.program.id}/enroll",
        }

        html_message = render_to_string('certificates/emails/expired.html', context)
        plain_message = f"""
        Hi {context['student_name']},

        Your OCH {track.name} Certificate (ID: {certificate.certificate_id_formatted})
        has expired and is no longer valid.

        To regain your certification, you will need to complete the re-certification process.

        Start re-certification: {context['recertification_url']}

        Best regards,
        Ongoza Cyber Hub Team
        """

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )

        logger.info(f"Sent expiration notification to {user.email} for cert {certificate.id}")

    @staticmethod
    def send_certificate_issued_notification(certificate):
        """Send certificate issued notification."""
        user = certificate.enrollment.user
        track = certificate.enrollment.cohort.track

        subject = f"Congratulations! Your OCH {track.name} Certificate is ready"

        context = {
            'student_name': user.first_name or user.email,
            'track_name': track.name,
            'certificate_id': certificate.certificate_id_formatted,
            'issue_date': certificate.issue_date,
            'expiry_date': certificate.expiry_date,
            'download_url': f"{settings.FRONTEND_URL}/api/v1/certificates/{certificate.id}/download",
            'verify_url': f"{settings.FRONTEND_URL}/verify/{certificate.id}",
        }

        html_message = render_to_string('certificates/emails/issued.html', context)
        plain_message = f"""
        Hi {context['student_name']},

        Congratulations! You have earned your OCH {track.name} Certificate.

        Certificate ID: {certificate.certificate_id_formatted}
        Issue Date: {certificate.issue_date}
        Valid Until: {certificate.expiry_date}

        Download your certificate: {context['download_url']}
        Verify your certificate: {context['verify_url']}

        Best regards,
        Ongoza Cyber Hub Team
        """

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )

        logger.info(f"Sent certificate issued notification to {user.email} for cert {certificate.id}")


# Convenience function for celery tasks
def check_certificate_notifications():
    """Entry point for scheduled certificate notification checks."""
    CertificateNotificationService.check_and_send_notifications()
