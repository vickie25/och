"""
Automated Billing Tasks - Celery tasks for subscription management
"""
from datetime import timedelta

from celery import shared_task
from django.db.models.functions import TruncDate
from django.utils import timezone

from .billing_engine import BillingPeriod, DunningSequence, EnhancedSubscription
from .billing_services import (
    UTC,
    BillingCycleManager,
    DunningManager,
    InvoiceGenerator,
    PaymentProcessor,
    SubscriptionLifecycleManager,
    utc_calendar_tomorrow,
)
from .email_service import SubscriptionEmailService
from .pdf_service import InvoicePDFGenerator


@shared_task
def process_subscription_renewals():
    """
    §3.1.3: Initiate renewal payment one calendar day before cycle end (UTC).
    On success, new period starts immediately (finalize). On failure, subscription stays on the
    current period until midnight UTC boundary enforcement moves unpaid cycles to PAST_DUE.
    Scheduled cancellations keep access until period end; status changes at boundary, not here.
    """
    tomorrow_utc = utc_calendar_tomorrow()

    expiring_subscriptions = (
        EnhancedSubscription.objects.annotate(
            _cycle_end_date_utc=TruncDate('current_period_end', tzinfo=UTC),
        )
        .filter(status='ACTIVE', _cycle_end_date_utc=tomorrow_utc, cancel_at_period_end=False)
    )

    results = []
    for subscription in expiring_subscriptions:
        try:
            plan_for_invoice = BillingCycleManager.effective_plan_version_at_next_boundary(
                subscription
            )
            billing_period = BillingCycleManager.create_upcoming_renewal_billing_period(subscription)
            invoice = InvoiceGenerator.create_subscription_invoice(
                billing_period, line_item_plan_version=plan_for_invoice
            )

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
                BillingCycleManager.finalize_renewal_after_payment(subscription, billing_period)

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
                billing_period.status = 'failed'
                billing_period.payment_failed_at = timezone.now()
                billing_period.save(update_fields=['status', 'payment_failed_at', 'updated_at'])

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
def enforce_subscription_cycle_boundary_utc():
    """
    §3.1.3: At/start after midnight UTC on cycle end, reconcile subscriptions whose current period
    has ended: scheduled cancel → CANCELED then EXPIRED; unpaid active cycles → PAST_DUE + dunning.
    """
    now = timezone.now().astimezone(UTC)
    start_today_utc = now.replace(hour=0, minute=0, second=0, microsecond=0)

    results = []

    # 1) Scheduled cancellation: period has ended (UTC day boundary)
    cancel_due = EnhancedSubscription.objects.filter(
        status='ACTIVE',
        cancel_at_period_end=True,
        current_period_end__lt=start_today_utc,
    )
    for subscription in cancel_due:
        try:
            subscription.transition_to('CANCELED', 'Billing period ended (scheduled cancellation)')
            if subscription.can_transition_to('EXPIRED'):
                subscription.transition_to('EXPIRED', 'Canceled subscription access period ended')
            results.append({'subscription_id': str(subscription.id), 'status': 'canceled_and_expired'})
        except Exception as e:
            results.append({
                'subscription_id': str(subscription.id),
                'status': 'error',
                'error': str(e),
            })

    # 2) Unpaid cycle: ACTIVE but period already ended (missed renewal or failed charge not yet reconciled)
    unpaid = EnhancedSubscription.objects.filter(
        status='ACTIVE',
        cancel_at_period_end=False,
        current_period_end__lt=start_today_utc,
    )
    for subscription in unpaid:
        try:
            next_end = subscription.calculate_next_billing_date()
            pv = BillingCycleManager.effective_plan_version_at_next_boundary(subscription)
            billing_period = BillingPeriod.objects.create(
                subscription=subscription,
                period_start=subscription.current_period_end,
                period_end=next_end,
                status='failed',
                amount=(
                    pv.price_monthly
                    if subscription.billing_cycle == 'monthly'
                    else pv.price_annual
                ),
                currency='KES',
                payment_failed_at=timezone.now(),
            )
            DunningManager.initiate_dunning_sequence(subscription, billing_period)
            results.append({'subscription_id': str(subscription.id), 'status': 'past_due_boundary'})
        except Exception as e:
            results.append({
                'subscription_id': str(subscription.id),
                'status': 'error',
                'error': str(e),
            })

    # 3) CANCELED with ended period → EXPIRED (end-of-access bookkeeping)
    for subscription in EnhancedSubscription.objects.filter(
        status='CANCELED',
        current_period_end__lt=start_today_utc,
    ):
        try:
            if subscription.can_transition_to('EXPIRED'):
                subscription.transition_to('EXPIRED', 'Billing period ended after cancellation')
                results.append({'subscription_id': str(subscription.id), 'status': 'expired_after_cancel'})
        except Exception as e:
            results.append({
                'subscription_id': str(subscription.id),
                'status': 'error',
                'error': str(e),
            })

    return {'processed': len(results), 'results': results}


@shared_task
def check_enhanced_academic_discount_expiry():
    """
    Enhanced academic discount re-verification:
      - Send reminders 30 days before expiry
      - Mark expired discounts
    Uses the academic discount model in `subscriptions.models`.
    """
    from datetime import timedelta

    from django.utils import timezone

    from .enhanced_billing_services import AcademicDiscountService
    from .models import AcademicDiscount

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
    """
    §3.1.5: Day 14 after initial payment failure — suspend account (access revoked).
    Retries at day 0 / 3 / 7 may already be exhausted; suspension is calendar-based from dunning start.
    """
    cutoff = timezone.now() - timedelta(days=14)
    due = (
        DunningSequence.objects.filter(
            status__in=('active', 'exhausted'),
            started_at__lte=cutoff,
        )
        .select_related('subscription')
        .order_by('started_at')
    )

    oldest_by_subscription = {}
    for d in due:
        oldest_by_subscription.setdefault(d.subscription_id, d)

    results = []
    for dunning in oldest_by_subscription.values():
        try:
            subscription = dunning.subscription
            if subscription.status != 'PAST_DUE':
                continue
            subscription.transition_to('SUSPENDED', 'Day 14 — unpaid after dunning sequence')

            dunning.status = 'exhausted'
            dunning.save(update_fields=['status', 'updated_at'])

            try:
                SubscriptionEmailService.send_account_suspended_dunning_email(subscription)
            except Exception:
                pass

            results.append({
                'subscription_id': str(subscription.id),
                'status': 'suspended'
            })
        except Exception as e:
            results.append({
                'subscription_id': str(dunning.subscription_id),
                'status': 'error',
                'error': str(e)
            })

    return {
        'processed': len(results),
        'results': results
    }


@shared_task
def send_suspended_reactivation_reminder_emails():
    """
    During SUSPENDED state: reminder emails on days 10, 20, and 25 of the 30-day reactivation window
    (from suspended_at).
    """
    now = timezone.now()
    results = []
    for subscription in EnhancedSubscription.objects.filter(
        status='SUSPENDED',
        suspended_at__isnull=False,
    ):
        try:
            if not subscription.reactivation_window_end or now > subscription.reactivation_window_end:
                continue
            days = max(0, (now.date() - subscription.suspended_at.date()).days)
            last = getattr(subscription, 'reactivation_reminder_last_milestone', 0) or 0
            for milestone in (10, 20, 25):
                if days >= milestone and last < milestone:
                    SubscriptionEmailService.send_suspended_reactivation_reminder(subscription, milestone)
                    subscription.reactivation_reminder_last_milestone = milestone
                    subscription.save(update_fields=['reactivation_reminder_last_milestone', 'updated_at'])
                    results.append({
                        'subscription_id': str(subscription.id),
                        'milestone': milestone,
                        'status': 'sent',
                    })
                    break
        except Exception as e:
            results.append({
                'subscription_id': str(subscription.id),
                'status': 'error',
                'error': str(e),
            })

    return {'processed': len(results), 'results': results}


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
    """
    §3.1.5: Grace-period reminders (monthly 3d / annual 7d) + Day-10 final suspension warning.
    """
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

            notification_type = None
            grace_blocked = (
                dunning.last_notification_sent
                and dunning.last_notification_sent.date() == now.date()
            )

            # Day 10 — final suspension warning (once; may fall same calendar day as other notices)
            if days_elapsed >= 10 and not dunning.suspension_warning_sent:
                SubscriptionEmailService.send_final_suspension_warning_email(
                    subscription, days_since_failure=days_elapsed
                )
                dunning.suspension_warning_sent = True
                notification_type = 'day_10_final_warning'

            # Grace reminders during 3-day (monthly) or 7-day (annual) grace window
            elif not grace_blocked and days_elapsed in (1, 3) and now <= dunning.grace_period_end:
                SubscriptionEmailService.send_grace_period_notification(
                    subscription,
                    day_number=days_elapsed,
                    days_remaining=days_remaining,
                    final_warning=False,
                )
                notification_type = f'grace_day_{days_elapsed}'

            elif not grace_blocked and days_remaining == 0 and not dunning.final_warning_sent and now.date() <= dunning.grace_period_end.date():
                SubscriptionEmailService.send_grace_period_notification(
                    subscription,
                    day_number=days_elapsed,
                    days_remaining=0,
                    final_warning=True,
                )
                dunning.final_warning_sent = True
                notification_type = 'grace_final_day'

            if notification_type:
                dunning.last_notification_sent = timezone.now()
                dunning.save(update_fields=['last_notification_sent', 'final_warning_sent', 'suspension_warning_sent', 'updated_at'])
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
