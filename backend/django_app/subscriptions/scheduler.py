"""
Subscription scheduler using django-apscheduler.
Runs periodic jobs that enforce billing business rules from the DSD spec:

  - attempt_subscription_renewals  (daily, 01:00 UTC)
      • Attempts payment 1 day before period_end for active subscriptions
      • Generates invoice on success
      • Creates retry schedule on failure

  - process_payment_retries  (every 6 hours)
      • Processes scheduled retry attempts
      • Retries on Day 1, 3, 5 after initial failure
      • Sends notifications

  - enforce_grace_period_and_downgrade  (every 12 hours)
      • past_due subscriptions past grace period → downgrade to Free Tier
      • canceled subscriptions past period_end → downgrade to Free Tier

  - check_academic_discount_expiry  (daily, 03:00 UTC)
      • Sends re-verification reminders 30 days before expiry
      • Marks expired discounts
"""
import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

def _add_months_anchored(dt, months: int, anchor_day: int):
    """Add months keeping a stable anchor day when possible."""
    import calendar
    year = dt.year + (dt.month - 1 + months) // 12
    month = (dt.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(anchor_day, last_day)
    return dt.replace(year=year, month=month, day=day)


# ── Job functions ─────────────────────────────────────────────────────────────

def enforce_grace_period_and_downgrade():
    """
    DSD §14.2 / §5.4.3:
      - Payment fails → grace period = 3 days (monthly) or 7 days (annual)
      - After grace period without success → status = canceled, downgrade to Free Tier

    Also handles:
      - Canceled subs whose period_end has passed → downgrade to Free Tier
    """
    from subscriptions.models import SubscriptionPlan, UserSubscription

    now = timezone.now()

    # -- 1. past_due past grace period → downgrade to Free ----------------
    try:
        free_plan = SubscriptionPlan.objects.get(tier='free')
    except SubscriptionPlan.DoesNotExist:
        logger.error('[scheduler] Free plan not found — cannot downgrade. Run seed_plans first.')
        return

    # Grace period: 3 days for monthly, 7 days for annual
    # Check if subscription is monthly or annual based on period length
    past_due_qs = UserSubscription.objects.filter(
        status='past_due',
    ).select_related('user', 'plan')

    for sub in past_due_qs:
        # Calculate grace period based on subscription type
        if sub.current_period_start and sub.current_period_end:
            period_days = (sub.current_period_end - sub.current_period_start).days
            grace_days = 7 if period_days > 180 else 3  # 7 for annual, 3 for monthly
        else:
            grace_days = 3  # Default to monthly

        # Notifications at day 1 and day 3 of grace; final warning on last day.
        try:
            from subscriptions.email_service import SubscriptionEmailService
            if sub.grace_period_end:
                grace_start = sub.grace_period_end - timedelta(days=grace_days)
                day_number = (now.date() - grace_start.date()).days
                days_remaining = max(0, (sub.grace_period_end.date() - now.date()).days)
                if day_number in [1, 3]:
                    SubscriptionEmailService.send_grace_period_notification(sub, day_number=day_number, days_remaining=days_remaining, final_warning=False)
                if days_remaining == 0:
                    SubscriptionEmailService.send_grace_period_notification(sub, day_number=day_number, days_remaining=days_remaining, final_warning=True)
        except Exception:
            pass

        if sub.grace_period_end and now >= sub.grace_period_end:
            old_plan = sub.plan.name
            sub.plan = free_plan
            sub.status = 'canceled'
            sub.enhanced_access_expires_at = None
            sub.save(update_fields=['plan', 'status', 'enhanced_access_expires_at', 'updated_at'])
            logger.info(
                f'[scheduler] Grace expired: {sub.user.email} downgraded '
                f'{old_plan} → free (past_due > {grace_days}d)'
            )

    # -- 2. canceled subs whose period has ended → move to free plan ------
    expired_canceled_qs = UserSubscription.objects.filter(
        status='canceled',
        current_period_end__lte=now,
    ).exclude(plan__tier='free').select_related('user', 'plan')

    for sub in expired_canceled_qs:
        old_plan = sub.plan.name
        sub.plan = free_plan
        sub.enhanced_access_expires_at = None
        sub.save(update_fields=['plan', 'enhanced_access_expires_at', 'updated_at'])
        logger.info(
            f'[scheduler] Canceled period ended: {sub.user.email} moved '
            f'{old_plan} → free'
        )

    # -- 3. pending downgrades at period end --------------------------------
    due_downgrades = UserSubscription.objects.filter(
        pending_downgrade_plan__isnull=False,
        current_period_end__lte=now,
        status__in=['active', 'past_due', 'trial', 'canceled'],
    ).select_related('user', 'plan', 'pending_downgrade_plan')

    for sub in due_downgrades:
        old_plan = sub.plan.name
        new_plan = sub.pending_downgrade_plan
        sub.plan = new_plan
        sub.pending_downgrade_plan = None
        sub.enhanced_access_expires_at = None
        sub.save(update_fields=['plan', 'pending_downgrade_plan', 'enhanced_access_expires_at', 'updated_at'])
        logger.info(f'[scheduler] Downgrade applied: {sub.user.email} {old_plan} → {new_plan.name}')


def attempt_subscription_renewals():
    """
    DSD §2.1.4: Auto-renewal logic
    Attempts payment 1 day before current_period_end for active subscriptions.

    Flow:
      1. Find subscriptions expiring in 1 day
      2. Attempt payment via gateway
      3. Success: Extend period, generate invoice, send email
      4. Failure: Mark past_due, create retry schedule
    """
    from subscriptions.models import (
        PaymentRetryAttempt,
        PaymentTransaction,
        SubscriptionInvoice,
        UserSubscription,
    )
    from subscriptions.utils import attempt_payment_charge, generate_invoice_pdf, send_invoice_email

    now = timezone.now()
    tomorrow = now + timedelta(days=1)

    # Find subscriptions expiring tomorrow
    due_qs = UserSubscription.objects.filter(
        status='active',
        current_period_end__date=tomorrow.date(),
    ).exclude(plan__tier='free').select_related('user', 'plan')

    for sub in due_qs:
        logger.info(f'[renewal] Attempting renewal for {sub.user.email} | {sub.plan.name}')

        # Calculate amount (monthly vs annual) with academic discount if applicable
        is_annual = getattr(sub, 'billing_interval', None) == 'annual' or getattr(sub.plan, 'billing_interval', None) == 'annual'
        if is_annual:
            amount = sub.plan.price_annual or 0
        else:
            amount = sub.plan.price_monthly or 0

        # Apply academic discount if active
        try:
            if hasattr(sub.user, 'academic_discount') and sub.user.academic_discount.is_active():
                amount = sub.user.academic_discount.calculate_discounted_price(amount)
                logger.info(f'[renewal] Academic discount applied: {amount} KES')
        except Exception as e:
            logger.warning(f'[renewal] Academic discount check failed: {e}')

        # Attempt payment
        try:
            success, transaction_id, error = attempt_payment_charge(
                user=sub.user,
                amount=amount,
                currency='KES',
                description=f'Subscription renewal - {sub.plan.name}'
            )

            if success:
                # Payment successful - extend subscription
                old_end = sub.current_period_end
                sub.current_period_start = sub.current_period_end
                # Calendar anchoring:
                # - monthly: same day-of-month as original end date (clamped for short months)
                # - annual: anniversary date (handles leap years by clamping)
                if is_annual:
                    try:
                        sub.current_period_end = sub.current_period_end.replace(year=sub.current_period_end.year + 1)
                    except ValueError:
                        # Feb 29 → Feb 28 on non-leap years
                        sub.current_period_end = sub.current_period_end.replace(year=sub.current_period_end.year + 1, month=2, day=28)
                else:
                    anchor_day = old_end.day if old_end else sub.current_period_end.day
                    sub.current_period_end = _add_months_anchored(sub.current_period_end, 1, anchor_day)
                sub.save(update_fields=['current_period_start', 'current_period_end', 'updated_at'])

                # Create payment transaction
                transaction = PaymentTransaction.objects.create(
                    user=sub.user,
                    subscription=sub,
                    amount=amount,
                    currency='KES',
                    status='completed',
                    gateway_transaction_id=transaction_id,
                    processed_at=now,
                )

                # Generate invoice
                invoice = SubscriptionInvoice.objects.create(
                    invoice_number=SubscriptionInvoice.generate_invoice_number(),
                    user=sub.user,
                    subscription=sub,
                    transaction=transaction,
                    status='paid',
                    subtotal=(sub.plan.price_annual if is_annual else (sub.plan.price_monthly or 0)) or 0,
                    discount_amount=(((sub.plan.price_annual if is_annual else (sub.plan.price_monthly or 0)) or 0) - amount),
                    total_amount=amount,
                    currency='KES',
                    invoice_date=now,
                    due_date=now,
                    paid_at=now,
                    line_items=[{
                        'description': f'{sub.plan.name} subscription',
                        'quantity': 1,
                        'unit_price': float((sub.plan.price_annual if is_annual else (sub.plan.price_monthly or 0)) or 0),
                        'total': float(amount),
                    }],
                )

                # Generate PDF and send email (async)
                try:
                    pdf_url = generate_invoice_pdf(invoice)
                    invoice.pdf_url = pdf_url
                    invoice.save(update_fields=['pdf_url'])
                    send_invoice_email(invoice)
                except Exception as e:
                    logger.error(f'[renewal] Invoice generation/email failed: {e}')

                logger.info(
                    f'[renewal] Success: {sub.user.email} | {sub.plan.name} | '
                    f'{old_end.date()} → {sub.current_period_end.date()} | Invoice: {invoice.invoice_number}'
                )
            else:
                # Payment failed - mark past_due and schedule retries
                sub.status = 'past_due'
                # Grace period end: 3 days monthly, 7 days annual
                grace_days = 7 if is_annual else 3
                sub.grace_period_end = now + timedelta(days=grace_days)
                sub.save(update_fields=['status', 'grace_period_end', 'updated_at'])

                # Create retry schedule: Day 1, 3, 5
                for retry_day in [1, 3, 5]:
                    PaymentRetryAttempt.objects.create(
                        subscription=sub,
                        attempt_number=retry_day,
                        status='pending',
                        amount=amount,
                        currency='KES',
                        scheduled_at=now + timedelta(days=retry_day),
                    )

                # Grace notifications: Day 1 and Day 3
                try:
                    from subscriptions.email_service import SubscriptionEmailService
                    SubscriptionEmailService.send_payment_failed_notification(sub, 1, 1)
                except Exception:
                    pass

                logger.warning(
                    f'[renewal] Failed: {sub.user.email} | {sub.plan.name} | '
                    f'Error: {error} | Retry schedule created'
                )

        except Exception as e:
            logger.error(f'[renewal] Exception for {sub.user.email}: {e}', exc_info=True)


def process_payment_retries():
    """
    DSD §3.1: Payment retry sequence
    Processes scheduled retry attempts for failed payments.

    Retry schedule: Day 1, 3, 5 after initial failure
    """
    from subscriptions.models import PaymentRetryAttempt, PaymentTransaction, SubscriptionInvoice
    from subscriptions.utils import attempt_payment_charge, send_retry_notification

    now = timezone.now()

    # Find pending retries that are due
    pending_retries = PaymentRetryAttempt.objects.filter(
        status='pending',
        scheduled_at__lte=now,
    ).select_related('subscription', 'subscription__user', 'subscription__plan')

    for retry in pending_retries:
        sub = retry.subscription
        logger.info(
            f'[retry] Attempt #{retry.attempt_number} for {sub.user.email} | {sub.plan.name}'
        )

        retry.status = 'processing'
        retry.attempted_at = now
        retry.save(update_fields=['status', 'attempted_at', 'updated_at'])

        try:
            success, transaction_id, error = attempt_payment_charge(
                user=sub.user,
                amount=retry.amount,
                currency=retry.currency,
                description=f'Retry #{retry.attempt_number} - {sub.plan.name}'
            )

            if success:
                # Retry successful - restore subscription
                retry.status = 'success'
                retry.completed_at = now
                retry.save(update_fields=['status', 'completed_at', 'updated_at'])

                # Restore subscription. Use billing interval to anchor period end.
                is_annual = getattr(sub, 'billing_interval', None) == 'annual' or getattr(sub.plan, 'billing_interval', None) == 'annual'
                sub.status = 'active'
                sub.current_period_start = now
                if is_annual:
                    try:
                        sub.current_period_end = now.replace(year=now.year + 1)
                    except ValueError:
                        sub.current_period_end = now.replace(year=now.year + 1, month=2, day=28)
                else:
                    sub.current_period_end = _add_months_anchored(now, 1, now.day)
                sub.save(update_fields=['status', 'current_period_start', 'current_period_end', 'updated_at'])

                # Create transaction and invoice
                transaction = PaymentTransaction.objects.create(
                    user=sub.user,
                    subscription=sub,
                    amount=retry.amount,
                    currency=retry.currency,
                    status='completed',
                    gateway_transaction_id=transaction_id,
                    processed_at=now,
                )

                invoice = SubscriptionInvoice.objects.create(
                    invoice_number=SubscriptionInvoice.generate_invoice_number(),
                    user=sub.user,
                    subscription=sub,
                    transaction=transaction,
                    status='paid',
                    subtotal=retry.amount,
                    total_amount=retry.amount,
                    currency=retry.currency,
                    invoice_date=now,
                    due_date=now,
                    paid_at=now,
                    line_items=[{
                        'description': f'{sub.plan.name} subscription (retry payment)',
                        'quantity': 1,
                        'unit_price': float(retry.amount),
                        'total': float(retry.amount),
                    }],
                )

                # Cancel remaining retries
                PaymentRetryAttempt.objects.filter(
                    subscription=sub,
                    status='pending',
                ).update(status='failed', error_message='Cancelled - earlier retry succeeded')

                logger.info(
                    f'[retry] Success: {sub.user.email} | Attempt #{retry.attempt_number} | '
                    f'Subscription restored | Invoice: {invoice.invoice_number}'
                )
            else:
                # Retry failed
                retry.status = 'failed'
                retry.completed_at = now
                retry.error_message = error or 'Payment failed'
                retry.save(update_fields=['status', 'completed_at', 'error_message', 'updated_at'])

                # Send notification
                send_retry_notification(sub.user, retry.attempt_number, error)

                logger.warning(
                    f'[retry] Failed: {sub.user.email} | Attempt #{retry.attempt_number} | '
                    f'Error: {error}'
                )

        except Exception as e:
            retry.status = 'failed'
            retry.completed_at = now
            retry.error_message = str(e)
            retry.save(update_fields=['status', 'completed_at', 'error_message', 'updated_at'])
            logger.error(f'[retry] Exception for {sub.user.email}: {e}', exc_info=True)


def check_academic_discount_expiry():
    """
    DSD §2.1.7: Academic discount re-verification
    Sends reminders 30 days before expiry and marks expired discounts.
    """
    from subscriptions.models import AcademicDiscount
    from subscriptions.utils import send_reverification_reminder

    now = timezone.now()
    reminder_date = now + timedelta(days=30)

    # Send reminders for discounts expiring in 30 days
    expiring_soon = AcademicDiscount.objects.filter(
        verification_status='verified',
        expires_at__date=reminder_date.date(),
    ).select_related('user')

    for discount in expiring_soon:
        try:
            send_reverification_reminder(discount.user, discount.expires_at)
            logger.info(f'[academic] Reminder sent to {discount.user.email} | Expires: {discount.expires_at.date()}')
        except Exception as e:
            logger.error(f'[academic] Reminder failed for {discount.user.email}: {e}')

    # Mark expired discounts
    expired = AcademicDiscount.objects.filter(
        verification_status='verified',
        expires_at__lte=now,
    ).select_related('user')

    for discount in expired:
        discount.verification_status = 'expired'
        discount.save(update_fields=['verification_status', 'updated_at'])
        logger.info(f'[academic] Expired: {discount.user.email} | Was valid until {discount.expires_at.date()}')


# ── Scheduler setup ───────────────────────────────────────────────────────────

def start():
    """
    Start APScheduler with the subscription jobs.
    Called from the subscriptions AppConfig.ready() hook.
    """
    import django_apscheduler.util as aputil
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from django_apscheduler.jobstores import DjangoJobStore
    from django_apscheduler.models import DjangoJobExecution

    scheduler = BackgroundScheduler(timezone='UTC')
    scheduler.add_jobstore(DjangoJobStore(), 'default')

    # Auto-renewal: daily at 01:00 UTC (attempt payment 1 day before expiry)
    scheduler.add_job(
        attempt_subscription_renewals,
        trigger=CronTrigger(hour=1, minute=0),
        id='attempt_renewals',
        max_instances=1,
        replace_existing=True,
    )

    # Payment retries: every 6 hours
    scheduler.add_job(
        process_payment_retries,
        trigger=CronTrigger(hour='*/6'),
        id='process_retries',
        max_instances=1,
        replace_existing=True,
    )

    # Grace-period enforcement: every 12 hours
    scheduler.add_job(
        enforce_grace_period_and_downgrade,
        trigger=CronTrigger(hour='*/12'),
        id='enforce_grace_period',
        max_instances=1,
        replace_existing=True,
    )

    # Academic discount expiry check: daily at 03:00 UTC
    scheduler.add_job(
        check_academic_discount_expiry,
        trigger=CronTrigger(hour=3, minute=0),
        id='check_academic_expiry',
        max_instances=1,
        replace_existing=True,
    )

    # Auto-cleanup old job execution records (keep 7 days)
    @aputil.close_old_connections
    def delete_old_job_executions(max_age=604800):
        DjangoJobExecution.objects.delete_old_job_executions(max_age)

    scheduler.add_job(
        delete_old_job_executions,
        trigger=CronTrigger(day_of_week='mon', hour=1),
        id='delete_old_job_executions',
        max_instances=1,
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        '[scheduler] APScheduler started: '
        'attempt_renewals (daily 01:00) + '
        'process_retries (6h) + '
        'enforce_grace_period (12h) + '
        'check_academic_expiry (daily 03:00)'
    )
