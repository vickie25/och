import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

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
        """§3.1.5: Email after each failed payment attempt with next steps and retry timing."""
        try:
            user = subscription.user
            context = {
                'user': user,
                'subscription': subscription,
                'retry_attempt': retry_attempt,
                'next_retry_days': next_retry_days,
                'update_payment_url': f"{settings.FRONTEND_URL.rstrip('/')}/billing/payment-methods"
            }

            html_content = render_to_string('subscriptions/emails/payment_failed.html', context)

            if next_retry_days is None:
                retry_msg = 'Our automated retry schedule has completed; please update your payment method or pay the open invoice to avoid suspension.'
            elif next_retry_days == 0:
                retry_msg = 'We will retry your payment automatically on the next collection run (Day 0 — immediate retry window).'
            else:
                retry_msg = f'We will make the next automatic retry {next_retry_days} day(s) after your first failed payment.'

            send_mail(
                subject=f'Payment failed — attempt {retry_attempt} (action needed)',
                message=(
                    f"Hi {user.first_name or user.email},\n\n"
                    f"We could not collect payment for your {getattr(subscription.plan_version, 'name', 'subscription')} plan.\n\n"
                    f"{retry_msg}\n\n"
                    f"Update your payment method here:\n{context['update_payment_url']}\n\n"
                    f"If you already updated your card, we will retry automatically.\n"
                ),
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
    def send_final_suspension_warning_email(subscription, days_since_failure: int):
        """§3.1.5 Day ~10: final warning before suspension (day 14)."""
        try:
            user = subscription.user
            base = getattr(settings, 'FRONTEND_URL', '').rstrip('/') or ''
            pay_url = f"{base}/billing/payment-methods"
            send_mail(
                subject='Final warning — subscription suspension scheduled',
                message=(
                    f"Hi {user.first_name or user.email},\n\n"
                    f"It has been about {days_since_failure} days since your payment failed. "
                    f"Per our policy, accounts that remain unpaid may be suspended for non-payment.\n\n"
                    f"Please update your payment method or pay your balance now:\n{pay_url}\n\n"
                    f"If payment is not received, your access may be revoked and you will receive suspension instructions.\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send final suspension warning to {subscription.user.email}: {str(e)}")
            return False

    @staticmethod
    def send_subscription_cancellation_confirmation(subscription, cancel_type, access_until=None):
        """
        Confirmation after user cancels: effective date, mode, reactivation / resubscribe guidance.
        cancel_type: 'immediate' | 'end_of_period'
        """
        try:
            user = subscription.user
            base = getattr(settings, 'FRONTEND_URL', '').rstrip('/') or ''
            billing_url = f"{base}/billing"
            reactivate_url = f"{base}/billing/reactivate"
            if cancel_type == 'immediate':
                mode = 'Immediate cancellation — access ends now.'
                refund_note = (
                    'Any refund will be processed according to our refund policy (typically no refund '
                    'for time already used in the billing period). Our team will notify you if a refund applies.'
                )
            else:
                mode = 'End-of-period cancellation — you keep full access until the end of your current billing period.'
                refund_note = 'No refund for the current period; you retain access through the paid-through date.'
            until = ''
            if access_until:
                until = f"\nAccess remains until: {access_until}\n"

            send_mail(
                subject='Subscription cancellation confirmed',
                message=(
                    f"Hi {user.first_name or user.email},\n\n"
                    f"We have received your cancellation request.\n\n"
                    f"{mode}\n"
                    f"{until}\n"
                    f"{refund_note}\n\n"
                    f"You may reverse an end-of-period cancellation anytime before access ends in Billing settings.\n"
                    f"Billing: {billing_url}\n\n"
                    f"If your account was suspended for payment, you can reactivate here while eligible:\n"
                    f"{reactivate_url}\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send cancellation confirmation to {subscription.user.email}: {str(e)}")
            return False

    @staticmethod
    def send_suspended_reactivation_reminder(subscription, day_milestone: int):
        """Reminders during 30-day suspension window (days 10, 20, 25 from suspension)."""
        try:
            user = subscription.user
            base = getattr(settings, 'FRONTEND_URL', '').rstrip('/') or ''
            pay_url = f"{base}/billing/payment-methods"
            reactivate_url = f"{base}/billing/reactivate"
            deadline = subscription.reactivation_window_end
            deadline_txt = deadline.strftime('%Y-%m-%d %H:%M UTC') if deadline else 'the end of your reactivation window'

            send_mail(
                subject=f'Reactivate your subscription (day {day_milestone} reminder)',
                message=(
                    f"Hi {user.first_name or user.email},\n\n"
                    f"Your subscription is still suspended. This is a reminder on day {day_milestone} of your "
                    f"30-day reactivation window.\n\n"
                    f"Pay your outstanding balance to restore access immediately:\n{reactivate_url}\n\n"
                    f"Update payment method: {pay_url}\n\n"
                    f"You must reactivate before {deadline_txt} or the subscription will expire and you will need a new subscription.\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send reactivation reminder to {subscription.user.email}: {str(e)}")
            return False

    @staticmethod
    def send_account_suspended_dunning_email(subscription):
        """§3.1.5: After suspension — amount context, reactivation, 30-day window."""
        try:
            user = subscription.user
            base = getattr(settings, 'FRONTEND_URL', '').rstrip('/') or ''
            pay_url = f"{base}/billing/payment-methods"
            reactivate_url = f"{base}/billing/reactivate"
            plan = getattr(subscription.plan_version, 'name', 'your plan')
            amount_hint = ''
            try:
                inv = subscription.invoices.order_by('-invoice_date').first()
                if inv:
                    amount_hint = f"Outstanding balance (latest invoice): {inv.total_amount} {inv.currency}.\n"
            except Exception:
                pass
            deadline = subscription.reactivation_window_end
            deadline_txt = deadline.strftime('%Y-%m-%d %H:%M UTC') if deadline else '30 days from suspension'

            send_mail(
                subject='Account suspended — payment required',
                message=(
                    f"Hi {user.first_name or user.email},\n\n"
                    f"Your subscription ({plan}) has been suspended due to unpaid charges after our retry period.\n\n"
                    f"{amount_hint}\n"
                    f"You have until {deadline_txt} to pay and reactivate before the subscription expires.\n\n"
                    f"Update payment method: {pay_url}\n"
                    f"Reactivate: {reactivate_url}\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send suspension email to {subscription.user.email}: {str(e)}")
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

    @staticmethod
    def send_grace_period_notification(subscription, day_number, days_remaining, final_warning=False):
        """
        Send grace period status notifications.
        Requirements:
          - day 1 + day 3 notifications
          - final warning on last day before suspension
        """
        try:
            user = subscription.user
            subject = "Payment Failed — Grace Period Active"
            if final_warning:
                subject = "FINAL WARNING — Subscription Suspension Imminent"
            message = (
                f"Hi {user.first_name or user.email},\n\n"
                f"Your recent subscription payment failed, but your access remains active during the grace period.\n\n"
                f"Grace day: {day_number}\n"
                f"Days remaining: {days_remaining}\n\n"
                f"Please update your payment method to avoid suspension.\n"
                f"{getattr(settings, 'FRONTEND_URL', '').rstrip('/')}/billing/payment-methods\n"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send grace notification to {subscription.user.email}: {str(e)}")
            return False

    @staticmethod
    def send_downgrade_scheduled_email(user, current_plan_name, new_plan_name, effective_date):
        """Notify user that a downgrade is scheduled for period end."""
        try:
            subject = "Downgrade scheduled"
            message = (
                f"Hi {user.first_name or user.email},\n\n"
                f"Your subscription downgrade is scheduled.\n\n"
                f"Current plan: {current_plan_name}\n"
                f"New plan: {new_plan_name}\n"
                f"Effective date: {effective_date.strftime('%Y-%m-%d')}\n\n"
                f"You can change your mind any time before then in your billing settings.\n"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send downgrade email to {user.email}: {str(e)}")
            return False
