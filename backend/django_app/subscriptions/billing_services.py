"""
Billing Engine Services - Core business logic for subscription management
"""
import calendar
from datetime import timedelta
from decimal import Decimal
import os
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .billing_engine import (
    BillingPeriod,
    DunningSequence,
    EnhancedSubscription,
    ProrationCredit,
    SubscriptionChange,
    SubscriptionInvoice,
)

UTC = ZoneInfo('UTC')


def utc_calendar_today():
    """Date in UTC for billing-cycle boundaries (§3.1.3)."""
    return timezone.now().astimezone(UTC).date()


def utc_calendar_tomorrow():
    return utc_calendar_today() + timedelta(days=1)


class SubscriptionLifecycleManager:
    """Manages subscription state transitions and lifecycle events."""

    @staticmethod
    def create_trial_subscription(user, plan_version, billing_cycle='monthly'):
        """Create new trial subscription."""
        trial_days = plan_version.trial_days
        trial_start = timezone.now()
        trial_end = trial_start + timedelta(days=trial_days)

        # Monthly anchor: signup calendar day (UTC) per §3.1.3
        last = calendar.monthrange(trial_start.year, trial_start.month)[1]
        cycle_anchor_day = min(trial_start.day, last)

        subscription = EnhancedSubscription.objects.create(
            user=user,
            plan_version=plan_version,
            status='TRIAL',
            billing_cycle=billing_cycle,
            cycle_anchor_day=cycle_anchor_day,
            current_period_start=trial_start,
            current_period_end=trial_end,
            trial_start=trial_start,
            trial_end=trial_end
        )

        # Create audit record
        SubscriptionChange.objects.create(
            subscription=subscription,
            change_type='status_change',
            old_value='',
            new_value=f'TRIAL:{plan_version.name}',
            reason='user_initiated',
            description=f'Trial subscription created for {plan_version.name}',
            created_by=user,
        )

        return subscription

    @staticmethod
    def convert_trial_to_active(subscription, converted_by=None):
        """Convert trial subscription to active with payment."""
        if subscription.status != 'TRIAL':
            raise ValidationError("Can only convert TRIAL subscriptions")

        period_start = timezone.now()
        period_end = BillingCycleManager.compute_first_paid_period_end(
            period_start,
            subscription.billing_cycle,
            subscription.cycle_anchor_day,
        )
        plan_name = subscription.plan_version.name
        old_label = f'TRIAL:{plan_name}'

        subscription.status = 'ACTIVE'
        subscription.current_period_start = period_start
        subscription.current_period_end = period_end
        subscription.save()

        amount = (
            subscription.plan_version.price_monthly
            if subscription.billing_cycle == 'monthly'
            else subscription.plan_version.price_annual
        )
        BillingPeriod.objects.create(
            subscription=subscription,
            period_start=period_start,
            period_end=period_end,
            status='completed',
            amount=amount,
            currency='KES',
            payment_completed_at=timezone.now(),
        )

        SubscriptionChange.objects.create(
            subscription=subscription,
            change_type='trial_conversion',
            old_value=old_label,
            new_value=f'ACTIVE:{plan_name}',
            proration_credit=None,
            proration_charge=amount,
            net_proration=amount,
            reason='trial_conversion',
            description=(
                f'Trial converted to paid subscription (first billing period). '
                f'Initiated by: {getattr(converted_by, "email", None) or "system/scheduler"}'
            ),
            created_by=converted_by,
        )

        return subscription


class BillingCycleManager:
    """Manages billing cycle calculations and renewals."""

    @staticmethod
    def calculate_next_billing_date(subscription):
        """Next period end from subscription.current_period_end (anchor-aware)."""
        return subscription.calculate_next_billing_date()

    @staticmethod
    def compute_first_paid_period_end(period_start, billing_cycle, cycle_anchor_day):
        """
        First paid cycle end from conversion time (monthly: next anchor calendar day; annual: +1 year).
        """
        if billing_cycle == 'annual':
            try:
                return period_start.replace(year=period_start.year + 1)
            except ValueError:
                return period_start.replace(year=period_start.year + 1, month=2, day=28)

        def clamp_day(year, month, anchor):
            last_day = calendar.monthrange(year, month)[1]
            return min(anchor, last_day)

        y, m = period_start.year, period_start.month
        d_this = clamp_day(y, m, cycle_anchor_day)
        candidate = period_start.replace(day=d_this)
        if candidate > period_start:
            return candidate
        if m == 12:
            y2, m2 = y + 1, 1
        else:
            y2, m2 = y, m + 1
        d2 = clamp_day(y2, m2, cycle_anchor_day)
        return period_start.replace(year=y2, month=m2, day=d2)

    @staticmethod
    def effective_plan_version_at_next_boundary(subscription):
        """Plan (and price) that applies at the upcoming period boundary, including scheduled downgrade."""
        next_start = subscription.current_period_end
        try:
            if (
                getattr(subscription, 'pending_downgrade_plan_version_id', None)
                and getattr(subscription, 'pending_downgrade_effective_at', None)
                and subscription.pending_downgrade_effective_at <= next_start
            ):
                return subscription.pending_downgrade_plan_version
        except Exception:
            pass
        return subscription.plan_version

    @staticmethod
    def create_upcoming_renewal_billing_period(subscription):
        """
        Build the next-cycle BillingPeriod for renewal charge (§3.1.3).
        Does not change subscription dates until payment succeeds — avoids advancing the cycle on failure.
        """
        if subscription.status != 'ACTIVE':
            raise ValidationError('Renewal requires ACTIVE subscription')

        next_period_start = subscription.current_period_end
        next_period_end = subscription.calculate_next_billing_date()
        plan_for_charge = BillingCycleManager.effective_plan_version_at_next_boundary(subscription)
        amount = (
            plan_for_charge.price_monthly
            if subscription.billing_cycle == 'monthly'
            else plan_for_charge.price_annual
        )
        return BillingPeriod.objects.create(
            subscription=subscription,
            period_start=next_period_start,
            period_end=next_period_end,
            status='upcoming',
            amount=amount,
            currency='KES',
        )

    @staticmethod
    def finalize_renewal_after_payment(subscription, billing_period):
        """
        After successful renewal charge: apply scheduled downgrade, advance subscription period,
        mark billing period completed (§3.1.3 — new period starts immediately on success).
        """
        with transaction.atomic():
            sub = EnhancedSubscription.objects.select_for_update().get(pk=subscription.pk)
            boundary = billing_period.period_start
            try:
                if (
                    getattr(sub, 'pending_downgrade_plan_version', None)
                    and getattr(sub, 'pending_downgrade_effective_at', None)
                    and sub.pending_downgrade_effective_at <= boundary
                ):
                    sub.plan_version = sub.pending_downgrade_plan_version
                    sub.pending_downgrade_plan_version = None
                    sub.pending_downgrade_effective_at = None
            except Exception:
                pass
            sub.current_period_start = billing_period.period_start
            sub.current_period_end = billing_period.period_end
            sub.save()
            billing_period.status = 'completed'
            billing_period.payment_completed_at = timezone.now()
            billing_period.save(update_fields=['status', 'payment_completed_at', 'updated_at'])

    @staticmethod
    def process_renewal(subscription):
        """
        Deprecated path: prefer create_upcoming_renewal_billing_period + charge + finalize_renewal_after_payment.
        Retained for callers that expect immediate period advance (not used by Celery renewal after refactor).
        """
        billing_period = BillingCycleManager.create_upcoming_renewal_billing_period(subscription)
        BillingCycleManager.finalize_renewal_after_payment(subscription, billing_period)
        return billing_period


class ProrationCalculator:
    """Handles proration calculations for mid-cycle plan changes (§3.1.4)."""

    @staticmethod
    def _plan_cycle_price(plan_version, billing_cycle):
        if billing_cycle == 'annual':
            return plan_version.price_annual or Decimal('0.00')
        return plan_version.price_monthly or Decimal('0.00')

    @staticmethod
    def calculate_upgrade_proration(subscription, new_plan_version):
        """
        Upgrade / lateral proration: credit = unused old plan value, charge = new plan for remaining
        calendar days in the cycle (matches day-based example in §3.1.4).
        Returns signed `net` (charge - credit); caller applies max(net,0) to collect and carry forward excess credit.
        """
        if subscription.status != 'ACTIVE':
            return {
                'credit': Decimal('0.00'),
                'charge': Decimal('0.00'),
                'net': Decimal('0.00'),
                'remaining_days': 0,
                'total_days': 0,
            }

        now = timezone.now()
        if now >= subscription.current_period_end:
            return {
                'credit': Decimal('0.00'),
                'charge': Decimal('0.00'),
                'net': Decimal('0.00'),
                'remaining_days': 0,
                'total_days': 0,
            }

        pstart = subscription.current_period_start.date()
        pend = subscription.current_period_end.date()
        today = now.date()
        total_days = max(1, (pend - pstart).days)
        remaining_days = max(0, (pend - today).days)

        current_price = ProrationCalculator._plan_cycle_price(
            subscription.plan_version, subscription.billing_cycle
        )
        new_price = ProrationCalculator._plan_cycle_price(new_plan_version, subscription.billing_cycle)

        current_daily = current_price / Decimal(total_days)
        new_daily = new_price / Decimal(total_days)

        credit = (current_daily * Decimal(remaining_days)).quantize(Decimal('0.01'))
        charge = (new_daily * Decimal(remaining_days)).quantize(Decimal('0.01'))
        net_charge = (charge - credit).quantize(Decimal('0.01'))

        return {
            'credit': credit,
            'charge': charge,
            'net': net_charge,
            'remaining_days': remaining_days,
            'total_days': total_days,
        }

    @staticmethod
    def apply_plan_change(subscription, new_plan_version, user=None):
        """
        Mid-cycle plan change (§3.1.4):
        - Downgrade (lower cycle price): effective at period end; no refund.
        - Upgrade / lateral: invoice shows credit + pro-rata charge; collect max(net,0) immediately;
          excess credit (net < 0) stored as pending ProrationCredit for the next invoice.
        """
        from .email_service import SubscriptionEmailService

        with transaction.atomic():
            old_plan = subscription.plan_version
            old_price = ProrationCalculator._plan_cycle_price(old_plan, subscription.billing_cycle)
            new_price = ProrationCalculator._plan_cycle_price(new_plan_version, subscription.billing_cycle)

            # Downgrade: no refund; change at period boundary only
            if new_price < old_price:
                subscription.pending_downgrade_plan_version = new_plan_version
                subscription.pending_downgrade_effective_at = subscription.current_period_end
                subscription.save(
                    update_fields=[
                        'pending_downgrade_plan_version',
                        'pending_downgrade_effective_at',
                        'updated_at',
                    ]
                )
                change_record = SubscriptionChange.objects.create(
                    subscription=subscription,
                    change_type='plan_change',
                    old_value=f'{old_plan.name} v{old_plan.version}',
                    new_value=f'{new_plan_version.name} v{new_plan_version.version}',
                    reason='user_initiated' if user else 'admin_initiated',
                    description='Downgrade scheduled for end of billing period (no refund)',
                    proration_credit=None,
                    proration_charge=None,
                    net_proration=None,
                    created_by=user,
                )
                try:
                    SubscriptionEmailService.send_downgrade_scheduled_email(
                        user=subscription.user,
                        current_plan_name=old_plan.name,
                        new_plan_name=new_plan_version.name,
                        effective_date=subscription.current_period_end or timezone.now(),
                    )
                except Exception:
                    pass
                return {
                    'subscription': subscription,
                    'proration': None,
                    'change_record': change_record,
                    'invoice': None,
                    'scheduled_downgrade': True,
                }

            proration = ProrationCalculator.calculate_upgrade_proration(subscription, new_plan_version)
            credit = proration['credit']
            charge = proration['charge']
            raw_net = proration['net']
            collect_now = max(Decimal('0.00'), raw_net)
            carry_forward = max(Decimal('0.00'), credit - charge)

            invoice = None
            billing_period = None
            if collect_now > 0:
                period_start = timezone.now()
                period_end = subscription.current_period_end
                billing_period = BillingPeriod.objects.create(
                    subscription=subscription,
                    period_start=period_start,
                    period_end=period_end,
                    status='current',
                    amount=collect_now,
                    currency='KES',
                )
                invoice = InvoiceGenerator.create_subscription_invoice(
                    billing_period,
                    line_item_plan_version=new_plan_version,
                    upgrade_proration={
                        'credit': credit,
                        'charge': charge,
                        'old_plan_name': old_plan.name,
                        'new_plan_name': new_plan_version.name,
                    },
                )
                billing_period.invoice = invoice
                billing_period.amount = invoice.total_amount
                billing_period.save(update_fields=['invoice', 'amount', 'updated_at'])

                billing_period.payment_attempted_at = timezone.now()
                billing_period.save(update_fields=['payment_attempted_at', 'updated_at'])
                success, _txn_id, error, _raw = PaymentProcessor.charge_subscription(
                    subscription,
                    amount=invoice.total_amount,
                    currency=invoice.currency or 'KES',
                    description=f'Upgrade proration charge {invoice.invoice_number}',
                )
                if not success:
                    billing_period.status = 'failed'
                    billing_period.payment_failed_at = timezone.now()
                    billing_period.save(update_fields=['status', 'payment_failed_at', 'updated_at'])
                    raise ValidationError(f'Upgrade payment failed: {error}')

                billing_period.status = 'completed'
                billing_period.payment_completed_at = timezone.now()
                billing_period.save(update_fields=['status', 'payment_completed_at', 'updated_at'])
                invoice.mark_as_paid()
                InvoiceGenerator.send_invoice(invoice)

            subscription.plan_version = new_plan_version
            subscription.save(update_fields=['plan_version', 'updated_at'])

            change_record = SubscriptionChange.objects.create(
                subscription=subscription,
                change_type='plan_change',
                old_value=f'{old_plan.name} v{old_plan.version}',
                new_value=f'{new_plan_version.name} v{new_plan_version.version}',
                reason='user_initiated' if user else 'admin_initiated',
                description=f'Plan changed from {old_plan.name} to {new_plan_version.name}',
                proration_credit=credit,
                proration_charge=charge,
                net_proration=raw_net,
                created_by=user,
            )

            if carry_forward > 0:
                ProrationCredit.objects.create(
                    subscription=subscription,
                    subscription_change=change_record,
                    amount=carry_forward,
                    currency='KES',
                    status='pending',
                )

            return {
                'subscription': subscription,
                'proration': proration,
                'change_record': change_record,
                'invoice': invoice,
                'carry_forward': carry_forward,
            }


class DunningManager:
    """Manages payment failure recovery and dunning sequences."""

    @staticmethod
    def initiate_dunning_sequence(subscription, billing_period):
        """Start dunning sequence for failed payment."""
        from .email_service import SubscriptionEmailService

        grace_days = 7 if subscription.billing_cycle == 'annual' else 3

        dunning = DunningSequence.objects.create(
            subscription=subscription,
            billing_period=billing_period,
            status='active',
            retry_schedule=[0, 3, 7],
            current_attempt=0,
            max_attempts=3,
            grace_period_days=grace_days,
            grace_period_end=timezone.now() + timedelta(days=grace_days),
            next_retry_at=timezone.now(),
        )

        subscription.transition_to('PAST_DUE', 'Payment failed, dunning sequence initiated')

        try:
            SubscriptionEmailService.send_payment_failed_notification(
                subscription, retry_attempt=0, next_retry_days=0
            )
        except Exception:
            pass

        return dunning

    @staticmethod
    def retry_after_payment_method_update(subscription):
        """
        §3.1.5: After user updates payment method during dunning, immediately attempt collection
        for the outstanding failed billing period (does not advance scheduled retry counter).
        """
        dunning = (
            DunningSequence.objects.filter(subscription=subscription, status='active')
            .order_by('-started_at')
            .first()
        )
        if not dunning:
            raise ValidationError('No active payment recovery in progress for this subscription')

        bp = dunning.billing_period
        invoice = getattr(bp, 'invoice', None)
        if invoice is None:
            try:
                invoice = SubscriptionInvoice.objects.get(billing_period=bp)
            except SubscriptionInvoice.DoesNotExist:
                invoice = InvoiceGenerator.create_subscription_invoice(bp)

        amount = invoice.total_amount
        if amount <= 0:
            raise ValidationError('No outstanding balance to charge')

        bp.payment_attempted_at = timezone.now()
        bp.save(update_fields=['payment_attempted_at', 'updated_at'])
        success, _txn_id, error, _raw = PaymentProcessor.charge_subscription(
            subscription,
            amount=amount,
            currency=invoice.currency or 'KES',
            description=f'Payment retry after method update {invoice.invoice_number}',
        )
        if not success:
            bp.status = 'failed'
            bp.payment_failed_at = timezone.now()
            bp.save(update_fields=['status', 'payment_failed_at', 'updated_at'])
            raise ValidationError(f'Payment failed: {error}')

        bp.status = 'completed'
        bp.payment_completed_at = timezone.now()
        bp.save(update_fields=['status', 'payment_completed_at', 'updated_at'])
        invoice.mark_as_paid()
        InvoiceGenerator.send_invoice(invoice)

        dunning.status = 'completed'
        dunning.completed_at = timezone.now()
        dunning.save(update_fields=['status', 'completed_at', 'updated_at'])
        subscription.transition_to('ACTIVE', 'Payment succeeded after payment method update')
        return {'subscription': subscription, 'invoice': invoice}

    @staticmethod
    def process_dunning_retries():
        """Process all pending dunning retries."""
        pending_retries = DunningSequence.objects.filter(
            status='active',
            next_retry_at__lte=timezone.now()
        )

        results = []
        for dunning in pending_retries:
            success = dunning.execute_retry()
            results.append({
                'dunning_id': dunning.id,
                'subscription_id': dunning.subscription.id,
                'attempt': dunning.current_attempt,
                'success': success
            })

        return results


class InvoiceGenerator:
    """Generates and manages subscription invoices."""

    @staticmethod
    def create_subscription_invoice(billing_period, line_item_plan_version=None, upgrade_proration=None):
        """Create invoice for billing period. Optional upgrade_proration applies §3.1.4 invoice credit lines."""
        subscription = billing_period.subscription

        if upgrade_proration:
            credit = upgrade_proration['credit']
            charge = upgrade_proration['charge']
            old_name = upgrade_proration['old_plan_name']
            new_name = upgrade_proration['new_plan_name']
            discount_amount = min(credit, charge)
            subtotal = charge
            tax_amount = Decimal('0.00')
            total_amount = max(Decimal('0.00'), charge - discount_amount)
            line_items = [
                {
                    'description': f'Credit — unused time on {old_name}',
                    'quantity': 1,
                    'unit_price': float(-discount_amount),
                    'total': float(-discount_amount),
                },
                {
                    'description': f'Charge — pro-rated {new_name} (remainder of cycle)',
                    'quantity': 1,
                    'unit_price': float(charge),
                    'total': float(charge),
                },
            ]
            invoice = SubscriptionInvoice.objects.create(
                subscription=subscription,
                billing_period=billing_period,
                invoice_number=SubscriptionInvoice.generate_invoice_number(),
                status='draft',
                subtotal=subtotal,
                discount_amount=discount_amount,
                tax_amount=tax_amount,
                total_amount=total_amount,
                currency='KES',
                due_date=timezone.now() + timedelta(days=7),
                line_items=line_items,
            )
        else:
            plan_label = (line_item_plan_version or subscription.plan_version).name
            subtotal = billing_period.amount
            tax_amount = Decimal('0.00')
            total_amount = subtotal + tax_amount
            invoice = SubscriptionInvoice.objects.create(
                subscription=subscription,
                billing_period=billing_period,
                invoice_number=SubscriptionInvoice.generate_invoice_number(),
                status='draft',
                subtotal=subtotal,
                discount_amount=Decimal('0.00'),
                tax_amount=tax_amount,
                total_amount=total_amount,
                currency='KES',
                due_date=timezone.now() + timedelta(days=7),
                line_items=[{
                    'description': f'{plan_label} - {subscription.billing_cycle.title()} Subscription',
                    'quantity': 1,
                    'unit_price': float(billing_period.amount),
                    'total': float(billing_period.amount)
                }]
            )

        invoice.apply_proration_credits()

        billing_period.invoice = invoice
        billing_period.save(update_fields=['invoice', 'updated_at'])

        return invoice

    @staticmethod
    def send_invoice(invoice):
        """Send invoice to customer."""
        # Add email sending logic here
        invoice.status = 'sent'
        invoice.sent_at = timezone.now()
        invoice.save()

        return True


class PaymentProcessor:
    """Gateway charge helpers for enhanced billing engine."""

    @staticmethod
    def charge_subscription(subscription: EnhancedSubscription, amount: Decimal, currency: str = 'usd', description: str = ''):
        """
        Attempt an off-session charge for an enhanced subscription.
        Returns: (success: bool, transaction_id: str|None, error: str|None, raw: dict|None)
        """
        # Single-gateway policy: Paystack only.
        gateway = (subscription.payment_gateway or 'paystack').lower()
        if gateway != 'paystack':
            return False, None, f'Unsupported gateway (expected paystack): {gateway}', None

        secret = os.environ.get('PAYSTACK_SECRET_KEY') or os.environ.get('PAYSTACK_SECRET')
        if not secret:
            return False, None, 'Paystack not configured (missing PAYSTACK_SECRET_KEY)', None

        authorization_code = (subscription.payment_method_ref or '').strip()
        if not authorization_code:
            return False, None, 'No Paystack authorization_code on file', None

        email = getattr(subscription.user, 'email', None) or ''
        if not email:
            return False, None, 'User email required for Paystack charge', None

        # Paystack expects smallest unit (kobo/cents). For KES, 1 KES = 100 “cents”.
        amount_in_cents = int((Decimal(amount) * 100).quantize(Decimal('1')))
        try:
            import requests
            resp = requests.post(
                "https://api.paystack.co/transaction/charge_authorization",
                headers={
                    'Authorization': f'Bearer {secret}',
                    'Content-Type': 'application/json',
                },
                json={
                    'authorization_code': authorization_code,
                    'email': email,
                    'amount': amount_in_cents,
                    'currency': (currency or 'KES').upper(),
                    'metadata': {'subscription_id': str(subscription.id), 'description': description},
                },
                timeout=15,
            )
            data = resp.json()
        except Exception as e:
            return False, None, str(e), None

        if not data.get('status'):
            return False, None, data.get('message') or 'Paystack charge_authorization failed', data

        inner = data.get('data') or {}
        if inner.get('status') != 'success':
            return False, None, f"Paystack status: {inner.get('status')}", data

        return True, inner.get('reference') or inner.get('id'), None, data


class ReactivationManager:
    """Reactivation flow for suspended subscriptions within window."""

    @staticmethod
    def reactivate(subscription, payment_method_ref=None, payment_gateway=None):
        """
        Charge outstanding balance and reactivate.
        Current implementation uses existing billing amount and records a paid invoice.
        """
        if subscription.status != 'SUSPENDED':
            raise ValidationError("Subscription is not suspended")
        if not subscription.reactivation_window_end or timezone.now() > subscription.reactivation_window_end:
            raise ValidationError("Reactivation window has expired")

        # Store payment method if provided
        if payment_method_ref:
            subscription.payment_method_ref = payment_method_ref
            subscription.payment_gateway = payment_gateway or subscription.payment_gateway
            subscription.payment_method_added_at = timezone.now()
            subscription.save(update_fields=['payment_method_ref', 'payment_gateway', 'payment_method_added_at', 'updated_at'])

        # Create a billing period/invoice for the outstanding amount
        period_start = timezone.now()
        period_end = BillingCycleManager.calculate_next_billing_date(subscription)
        billing_period = BillingPeriod.objects.create(
            subscription=subscription,
            period_start=period_start,
            period_end=period_end,
            status='current',
            amount=subscription.plan_version.price_monthly if subscription.billing_cycle == 'monthly' else subscription.plan_version.price_annual,
            currency='KES',
        )
        invoice = InvoiceGenerator.create_subscription_invoice(billing_period)

        # Charge via gateway before marking paid
        billing_period.payment_attempted_at = timezone.now()
        billing_period.save(update_fields=['payment_attempted_at', 'updated_at'])
        success, txn_id, error, _raw = PaymentProcessor.charge_subscription(
            subscription,
            amount=invoice.total_amount,
            currency=invoice.currency or 'KES',
            description=f'Reactivation charge {invoice.invoice_number}',
        )
        if not success:
            billing_period.status = 'failed'
            billing_period.payment_failed_at = timezone.now()
            billing_period.save(update_fields=['status', 'payment_failed_at', 'updated_at'])
            raise ValidationError(f'Payment failed: {error}')

        billing_period.status = 'completed'
        billing_period.payment_completed_at = timezone.now()
        billing_period.save(update_fields=['status', 'payment_completed_at', 'updated_at'])
        invoice.mark_as_paid()
        InvoiceGenerator.send_invoice(invoice)

        subscription.transition_to('ACTIVE', 'Reactivated by payment')
        return {'subscription': subscription, 'invoice': invoice, 'billing_period': billing_period}


class CancellationPolicy:
    """
    Refund behavior for immediate cancellation (policy-driven).
    Default: no automatic gateway refund; finance uses admin tools / gateway dashboard if a refund applies.
    """

    @staticmethod
    def process_immediate_refund_if_applicable(subscription):
        """
        Returns a result dict. Extend here to call Paystack/Stripe partial refunds when policy allows.
        """
        return {
            'refund_issued': False,
            'detail': 'No automatic refund issued. Refunds when applicable are processed per refund policy '
            '(typically no refund for time already used in the paid period).',
        }
