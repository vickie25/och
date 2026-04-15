"""
Automated Billing Tasks - Celery tasks for subscription management
"""
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .billing_engine import BillingPeriod, DunningSequence, EnhancedSubscription
from .billing_services import (
    BillingCycleManager,
    DunningManager,
    InvoiceGenerator,
    PaymentProcessor,
    SubscriptionLifecycleManager,
)
from .email_service import SubscriptionEmailService
from .pdf_service import InvoicePDFGenerator


@shared_task
def process_subscription_renewals():
    """Process subscription renewals 1 day before period end."""
    tomorrow = timezone.now() + timedelta(days=1)

    # Find subscriptions ending tomorrow
    expiring_subscriptions = EnhancedSubscription.objects.filter(
        status='ACTIVE',
        current_period_end__date=tomorrow.date()
    )

    results = []
    for subscription in expiring_subscriptions:
        try:
            # Respect end-of-period cancellations: do not renew.
            if subscription.cancel_at_period_end:
                subscription.transition_to('CANCELED', 'Canceled at period end')
                results.append({
                    'subscription_id': str(subscription.id),
                    'status': 'canceled_at_period_end'
                })
                continue

            # Attempt to charge for renewal
            billing_period = BillingCycleManager.process_renewal(subscription)

            # Generate invoice
            invoice = InvoiceGenerator.create_subscription_invoice(billing_period)

            # Attempt payment via real gateway
            billing_period.payment_attempted_at = timezone.now()
            billing_period.save(update_fields=['payment_attempted_at', 'updated_at'])
            payment_success, txn_id, error, _raw = PaymentProcessor.charge_subscription(
                subscription,
                amount=invoice.total_amount,
                currency=invoice.currency or 'KES',
                description=f'Renewal charge {invoice.invoice_number}',
            )

            if payment_success:
                invoice.mark_as_paid()
                billing_period.status = 'completed'
                billing_period.payment_completed_at = timezone.now()
                billing_period.save()

                # Send invoice (PDF + email)
                try:
                    # We don't persist the PDF binary; we rely on the frontend/pdf endpoint URL.
                    # Generating the PDF here sanity-checks that invoice details are renderable.
                    InvoicePDFGenerator.generate_invoice_pdf(invoice)
                    InvoiceGenerator.send_invoice(invoice)  # marks sent
                    SubscriptionEmailService.send_invoice_email(subscription, invoice)
                except Exception:
                    # Never block renewal success on email/PDF issues
                    pass

                results.append({
                    'subscription_id': str(subscription.id),
                    'status': 'success',
                    'invoice_id': str(invoice.id)
                })
            else:
                # Payment failed - initiate dunning
                billing_period.status = 'failed'
                billing_period.payment_failed_at = timezone.now()
                billing_period.save()

                dunning = DunningManager.initiate_dunning_sequence(subscription, billing_period)

                results.append({
                    'subscription_id': str(subscription.id),
                    'status': 'payment_failed',
                    'dunning_id': str(dunning.id)
                })

        except Exception as e:
            results.append({
                'subscription_id': str(subscription.id),
                'status': 'error',
                'error': str(e)
            })

    return {
        'processed': len(results),
        'results': results
    }


@shared_task
def check_enhanced_academic_discount_expiry():
    """
    Enhanced academic discount re-verification:
      - Send reminders 30 days before expiry
      - Mark expired discounts
    Uses the enhanced academic discount model in `promotional_models.py`.
    """
    from datetime import timedelta

    from django.utils import timezone

    from .enhanced_billing_services import AcademicDiscountService
    from .promotional_models import AcademicDiscount

    now = timezone.now()

    # Reminders for discounts expiring in the next 30 days (once)
    expiring_soon = AcademicDiscount.objects.filter(
        status='verified',
        expires_at__lte=now + timedelta(days=30),
        expires_at__gt=now,
        last_reverification_sent__isnull=True,
    ).select_related('user')

    for discount in expiring_soon:
        try:
            discount.send_reverification_reminder()
            AcademicDiscountService._send_reverification_email(discount)
        except Exception:
            continue

    # Mark expired
    expired = AcademicDiscount.objects.filter(
        status='verified',
        expires_at__lte=now,
    )
    for discount in expired:
        discount.status = 'expired'
        discount.save(update_fields=['status', 'updated_at'])

    return {
        'reminded': expiring_soon.count(),
        'expired': expired.count(),
    }


@shared_task
def process_dunning_retries():
    """Process dunning retry attempts."""
    results = DunningManager.process_dunning_retries()

    return {
        'processed': len(results),
        'results': results
    }


@shared_task
def expire_trial_subscriptions():
    """Convert expired trials to active (if card-on-file) or expired."""
    expired_trials = EnhancedSubscription.objects.filter(
        status='TRIAL',
        trial_end__lt=timezone.now()
    )

    results = []
    for subscription in expired_trials:
        try:
            # If the trial has a payment method on file, auto-convert to paid.
            if subscription.payment_method_ref:
                SubscriptionLifecycleManager.convert_trial_to_active(subscription)
                results.append({
                    'subscription_id': str(subscription.id),
                    'status': 'converted_to_active'
                })
                continue

            subscription.transition_to('EXPIRED', 'Trial period expired')
            results.append({
                'subscription_id': str(subscription.id),
                'status': 'expired'
            })
        except Exception as e:
            results.append({
                'subscription_id': str(subscription.id),
                'status': 'error',
                'error': str(e)
            })

    return {
        'processed': len(results),
        'results': results
    }


@shared_task
def suspend_past_due_subscriptions():
    """Suspend subscriptions that are past grace period."""
    grace_expired = DunningSequence.objects.filter(
        status='active',
        grace_period_end__lt=timezone.now(),
        current_attempt__gte=3  # All retries exhausted
    )

    results = []
    for dunning in grace_expired:
        try:
            subscription = dunning.subscription
            subscription.transition_to('SUSPENDED', 'Grace period expired, all retries failed')

            dunning.status = 'exhausted'
            dunning.save()

            results.append({
                'subscription_id': str(subscription.id),
                'status': 'suspended'
            })
        except Exception as e:
            results.append({
                'subscription_id': str(subscription.id),
                'status': 'error',
                'error': str(e)
            })

    return {
        'processed': len(results),
        'results': results
    }


@shared_task
def expire_suspended_subscriptions():
    """Expire subscriptions after 30-day reactivation window."""
    reactivation_expired = EnhancedSubscription.objects.filter(
        status='SUSPENDED',
        reactivation_window_end__lt=timezone.now()
    )

    results = []
    for subscription in reactivation_expired:
        try:
            subscription.transition_to('EXPIRED', '30-day reactivation window expired')
            results.append({
                'subscription_id': str(subscription.id),
                'status': 'expired'
            })
        except Exception as e:
            results.append({
                'subscription_id': str(subscription.id),
                'status': 'error',
                'error': str(e)
            })

    return {
        'processed': len(results),
        'results': results
    }


@shared_task
def send_dunning_notifications():
    """Send dunning notification emails."""
    # Find subscriptions needing notifications
    active_dunning = DunningSequence.objects.filter(
        status='active'
    ).select_related('subscription__user')

    results = []
    for dunning in active_dunning:
        try:
            subscription = dunning.subscription
            now = timezone.now()
            days_elapsed = max(0, (now.date() - dunning.started_at.date()).days)
            days_remaining = max(0, (dunning.grace_period_end.date() - now.date()).days)

            # Only send once per day
            if dunning.last_notification_sent and dunning.last_notification_sent.date() == now.date():
                continue

            # Day 1 and Day 3 grace notifications
            if days_elapsed in [1, 3]:
                SubscriptionEmailService.send_grace_period_notification(
                    subscription,
                    day_number=days_elapsed,
                    days_remaining=days_remaining,
                    final_warning=False
                )
                notification_type = f'grace_day_{days_elapsed}'

            # Final warning on last day before suspension
            elif days_remaining == 0 and not dunning.final_warning_sent:
                SubscriptionEmailService.send_grace_period_notification(
                    subscription,
                    day_number=days_elapsed,
                    days_remaining=days_remaining,
                    final_warning=True
                )
                dunning.final_warning_sent = True
                notification_type = 'final_warning'
            else:
                continue

            dunning.last_notification_sent = timezone.now()
            dunning.save(update_fields=['last_notification_sent', 'final_warning_sent', 'updated_at'])

            results.append({
                'subscription_id': str(subscription.id),
                'notification_type': notification_type,
                'status': 'sent'
            })

        except Exception as e:
            results.append({
                'subscription_id': str(subscription.id),
                'status': 'error',
                'error': str(e)
            })

    return {
        'processed': len(results),
        'results': results
    }


@shared_task
def generate_monthly_billing_report():
    """Generate monthly billing analytics report."""
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Subscription metrics
    total_subscriptions = EnhancedSubscription.objects.count()
    active_subscriptions = EnhancedSubscription.objects.filter(status='ACTIVE').count()
    trial_subscriptions = EnhancedSubscription.objects.filter(status='TRIAL').count()
    past_due_subscriptions = EnhancedSubscription.objects.filter(status='PAST_DUE').count()
    suspended_subscriptions = EnhancedSubscription.objects.filter(status='SUSPENDED').count()

    # Revenue metrics
    monthly_invoices = BillingPeriod.objects.filter(
        created_at__gte=month_start,
        status='completed'
    )
    monthly_revenue = sum(period.amount for period in monthly_invoices)

    # Dunning metrics
    active_dunning = DunningSequence.objects.filter(status='active').count()
    successful_recoveries = DunningSequence.objects.filter(
        status='completed',
        completed_at__gte=month_start
    ).count()

    report = {
        'period': f"{month_start.strftime('%Y-%m')}",
        'subscription_metrics': {
            'total': total_subscriptions,
            'active': active_subscriptions,
            'trial': trial_subscriptions,
            'past_due': past_due_subscriptions,
            'suspended': suspended_subscriptions
        },
        'revenue_metrics': {
            'monthly_revenue': float(monthly_revenue),
            'completed_billing_periods': monthly_invoices.count()
        },
        'dunning_metrics': {
            'active_dunning_sequences': active_dunning,
            'successful_recoveries': successful_recoveries
        },
        'generated_at': now.isoformat()
    }

    return report


def _attempt_payment(subscription, invoice):
    """Deprecated: use PaymentProcessor.charge_subscription()."""
    success, _txn, _err, _raw = PaymentProcessor.charge_subscription(
        subscription, amount=invoice.total_amount, currency=invoice.currency or 'usd'
    )
    return success


def _send_payment_failed_email(user, subscription, dunning):
    """Deprecated: kept for backward compatibility."""
    return SubscriptionEmailService.send_grace_period_notification(subscription, day_number=1, days_remaining=dunning.grace_period_days)


def _send_retry_failed_email(user, subscription, dunning):
    """Deprecated: kept for backward compatibility."""
    return SubscriptionEmailService.send_grace_period_notification(subscription, day_number=3, days_remaining=0)


def _send_suspension_warning_email(user, subscription, dunning):
    """Deprecated: kept for backward compatibility."""
    return SubscriptionEmailService.send_grace_period_notification(subscription, day_number=dunning.grace_period_days, days_remaining=0, final_warning=True)
