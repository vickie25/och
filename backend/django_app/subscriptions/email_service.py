from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

class SubscriptionEmailService:
    @staticmethod
    def send_payment_reminder(subscription):
        """Send payment reminder 1 day before renewal"""
        try:
            user = subscription.user
            context = {
                'user': user,
                'subscription': subscription,
                'update_payment_url': f"{settings.FRONTEND_URL}/billing/payment-methods"
            }
            
            html_content = render_to_string('subscriptions/emails/payment_reminder.html', context)
            
            send_mail(
                subject='Payment Reminder - Subscription Renewal Tomorrow',
                message='Your subscription will renew tomorrow. Please ensure your payment method is up to date.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Payment reminder sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send payment reminder to {subscription.user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_payment_failed_notification(subscription, retry_attempt, next_retry_days):
        """Send payment failed notification with retry info"""
        try:
            user = subscription.user
            context = {
                'user': user,
                'subscription': subscription,
                'retry_attempt': retry_attempt,
                'next_retry_days': next_retry_days,
                'update_payment_url': f"{settings.FRONTEND_URL}/billing/payment-methods"
            }
            
            html_content = render_to_string('subscriptions/emails/payment_failed.html', context)
            
            send_mail(
                subject=f'Payment Failed - Retry Attempt {retry_attempt}',
                message=f'Your subscription payment failed. We will retry in {next_retry_days} days.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Payment failed notification sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send payment failed notification to {subscription.user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_invoice_email(subscription, invoice):
        """Send invoice after successful payment"""
        try:
            user = subscription.user
            context = {
                'user': user,
                'subscription': subscription,
                'invoice': invoice,
                'invoice_pdf_url': f"{settings.FRONTEND_URL}/billing/invoices/{invoice.id}/pdf"
            }
            
            html_content = render_to_string('subscriptions/emails/invoice.html', context)
            
            send_mail(
                subject=f'Invoice #{invoice.invoice_number} - Payment Successful',
                message='Your payment was successful. Please find your invoice attached.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Invoice email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send invoice email to {subscription.user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_subscription_cancelled_notification(subscription):
        """Send notification when subscription is cancelled due to payment failures"""
        try:
            user = subscription.user
            
            send_mail(
                subject='Subscription Cancelled - Payment Failed',
                message=f'Your {subscription.plan_type} subscription has been cancelled due to payment failures. You can reactivate anytime.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False
            )
            
            logger.info(f"Cancellation notification sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send cancellation notification to {subscription.user.email}: {str(e)}")
            return False