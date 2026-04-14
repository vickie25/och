"""
Subscription-related Celery tasks
"""
import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Subscription

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def check_subscription_renewals(self):
    """
    Check for subscriptions that need renewal processing
    """
    try:
        # Find subscriptions expiring in the next 24 hours
        tomorrow = timezone.now() + timezone.timedelta(days=1)
        expiring_subscriptions = Subscription.objects.filter(
            end_date__lte=tomorrow,
            status='active'
        )

        processed_count = 0
        for subscription in expiring_subscriptions:
            # Process renewal logic
            send_renewal_reminder.delay(subscription.id)
            processed_count += 1

        logger.info(f"Processed {processed_count} subscription renewals")
        return f"Processed {processed_count} renewals"

    except Exception as exc:
        logger.error(f"Subscription renewal check failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task(bind=True, max_retries=3)
def send_renewal_reminder(self, subscription_id):
    """
    Send renewal reminder email to user
    """
    try:
        subscription = Subscription.objects.get(id=subscription_id)
        user = subscription.user

        subject = "Your OCH Subscription is Expiring Soon"
        message = f"""
        Hi {user.first_name},

        Your OCH subscription will expire on {subscription.end_date.strftime('%B %d, %Y')}.

        To continue accessing premium features, please renew your subscription.

        Best regards,
        OCH Team
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f"Renewal reminder sent to {user.email}")
        return f"Reminder sent to {user.email}"

    except Subscription.DoesNotExist:
        logger.error(f"Subscription {subscription_id} not found")
        return f"Subscription {subscription_id} not found"
    except Exception as exc:
        logger.error(f"Failed to send renewal reminder: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task
def process_grace_period_expiry():
    """
    Process subscriptions that have exceeded grace period
    """
    try:
        # Find subscriptions in grace period that have expired
        grace_period_expired = Subscription.objects.filter(
            status='grace_period',
            end_date__lt=timezone.now() - timezone.timedelta(days=7)  # 7-day grace period
        )

        processed_count = 0
        for subscription in grace_period_expired:
            # Deactivate subscription
            subscription.status = 'expired'
            subscription.save()

            # Send final notice
            send_subscription_expired_notice.delay(subscription.id)
            processed_count += 1

        logger.info(f"Processed {processed_count} expired subscriptions")
        return f"Processed {processed_count} expired subscriptions"

    except Exception as exc:
        logger.error(f"Grace period processing failed: {exc}")
        raise exc

@shared_task(bind=True, max_retries=2)
def send_subscription_expired_notice(self, subscription_id):
    """
    Send final expiration notice to user
    """
    try:
        subscription = Subscription.objects.get(id=subscription_id)
        user = subscription.user

        subject = "Your OCH Subscription Has Expired"
        message = f"""
        Hi {user.first_name},

        Your OCH subscription has expired. You now have limited access to platform features.

        To restore full access, please renew your subscription at your earliest convenience.

        Best regards,
        OCH Team
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f"Expiration notice sent to {user.email}")
        return f"Expiration notice sent to {user.email}"

    except Exception as exc:
        logger.error(f"Failed to send expiration notice: {exc}")
        raise self.retry(exc=exc, countdown=120)
