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
)


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
            # Attempt to charge for renewal
            billing_period = BillingCycleManager.process_renewal(subscription)

            # Generate invoice
            invoice = InvoiceGenerator.create_subscription_invoice(billing_period)

            # Attempt payment (placeholder - integrate with actual payment gateway)
            payment_success = _attempt_payment(subscription, invoice)

            if payment_success:
                invoice.mark_as_paid()
                billing_period.status = 'completed'
                billing_period.payment_completed_at = timezone.now()
                billing_period.save()

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
def process_dunning_retries():
    """Process dunning retry attempts."""
    results = DunningManager.process_dunning_retries()

    return {
        'processed': len(results),
        'results': results
    }


@shared_task
def expire_trial_subscriptions():
    """Convert expired trials to expired status."""
    expired_trials = EnhancedSubscription.objects.filter(
        status='TRIAL',
        trial_end__lt=timezone.now()
    )

    results = []
    for subscription in expired_trials:
        try:
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
            user = subscription.user

            # Determine notification type
            if dunning.current_attempt == 1 and not dunning.last_notification_sent:
                # First failure notification
                _send_payment_failed_email(user, subscription, dunning)
                notification_type = 'payment_failed'

            elif dunning.current_attempt == 2:
                # Second attempt notification
                _send_retry_failed_email(user, subscription, dunning)
                notification_type = 'retry_failed'

            elif dunning.current_attempt >= 3 and not dunning.suspension_warning_sent:
                # Suspension warning
                _send_suspension_warning_email(user, subscription, dunning)
                dunning.suspension_warning_sent = True
                notification_type = 'suspension_warning'

            else:
                continue

            dunning.last_notification_sent = timezone.now()
            dunning.save()

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
    """Placeholder for payment processing integration."""
    # This would integrate with Stripe, Paystack, etc.
    # For now, simulate payment success/failure
    import random
    return random.choice([True, False])  # 50% success rate for simulation


def _send_payment_failed_email(user, subscription, dunning):
    """Send payment failed notification email."""
    # Implement email sending logic
    pass


def _send_retry_failed_email(user, subscription, dunning):
    """Send retry failed notification email."""
    # Implement email sending logic
    pass


def _send_suspension_warning_email(user, subscription, dunning):
    """Send suspension warning email."""
    # Implement email sending logic
    pass
