"""
Test Celery tasks to verify the setup is working
"""
import logging
import time

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

@shared_task
def test_basic_task():
    """
    Simple test task to verify Celery is working
    """
    logger.info("Test task started")
    time.sleep(2)  # Simulate some work
    logger.info("Test task completed")
    return "Test task completed successfully!"

@shared_task
def test_email_task(recipient_email):
    """
    Test email sending task
    """
    try:
        subject = "OCH Platform - Celery Test Email"
        message = """
        This is a test email from the OCH Platform Celery system.

        If you received this email, it means:
        ✅ Celery is working correctly
        ✅ Redis is connected
        ✅ Email configuration is working

        Time sent: {}
        """.format(time.strftime("%Y-%m-%d %H:%M:%S"))

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )

        logger.info(f"Test email sent to {recipient_email}")
        return f"Test email sent successfully to {recipient_email}"

    except Exception as exc:
        logger.error(f"Failed to send test email: {exc}")
        raise exc

@shared_task
def test_long_running_task():
    """
    Test a longer running task to verify worker stability
    """
    logger.info("Long running task started")

    for i in range(10):
        time.sleep(1)
        logger.info(f"Long task progress: {i+1}/10")

    logger.info("Long running task completed")
    return "Long running task completed after 10 seconds!"

@shared_task(bind=True, max_retries=3)
def test_retry_task(self, should_fail=True):
    """
    Test task retry functionality
    """
    try:
        if should_fail and self.request.retries < 2:
            logger.warning(f"Task failing intentionally (retry {self.request.retries})")
            raise Exception("Intentional failure for testing")

        logger.info("Retry task succeeded!")
        return f"Task succeeded after {self.request.retries} retries"

    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc, countdown=5)  # Retry after 5 seconds
